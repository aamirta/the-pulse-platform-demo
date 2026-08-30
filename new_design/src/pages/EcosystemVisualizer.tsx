import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Search,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Network,
  Info,
  ArrowRight,
  Filter,
  Sparkles,
  AlertTriangle,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useTheme } from '@/hooks/useTheme';
import { useLanguage } from '@/context/LanguageContext';
import { useEcosystemGraph } from '@/hooks/useEcosystemGraph';
import type { GraphLinkType, GraphNodeType } from '@/types';

interface SimNode {
  id: string;
  name: string;
  type: GraphNodeType;
  refId: string;
  sector?: string | null;
  location?: string | null;
  connectionsCount: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  color: string;
}

interface SimLink {
  source: string;
  target: string;
  type: GraphLinkType;
}

interface PulseParticle {
  linkIndex: number;
  progress: number;
  speed: number;
}

type FilterId = 'all' | GraphNodeType;

const NODE_COLORS: Record<GraphNodeType, string> = {
  startup: '#d56426',
  founder: '#3b82f6',
  investor: '#10b981',
  incubator: '#a855f7',
};

const LINK_COLORS: Record<GraphLinkType, string> = {
  founded: '#3b82f6',
  invested: '#10b981',
  incubated: '#a855f7',
  // Incubator -> founder affiliation, the only edge that skips the startup.
  supported: '#f59e0b',
};

/** Ideal on-screen length per relationship type, used by the spring force. */
const LINK_DISTANCE: Record<GraphLinkType, number> = {
  founded: 80,
  invested: 155,
  incubated: 130,
  supported: 110,
};

/**
 * Deterministic 0..1 hash of a node id.
 *
 * Seeding the initial layout from the id (instead of Math.random) keeps the
 * graph reproducible between reloads, so a given entity lands in a familiar
 * place every time.
 */
function seededUnit(id: string, salt: number): number {
  let h = 2166136261 ^ salt;
  for (let i = 0; i < id.length; i++) {
    h ^= id.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 10000) / 10000;
}

export default function EcosystemVisualizer() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { theme } = useTheme();
  const { t, language } = useLanguage();
  const isFr = language === 'fr';
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const { data: graph, isLoading, error } = useEcosystemGraph();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<FilterId>('all');
  // Bumped whenever the simulation is rebuilt, so UI derived from the node
  // ref re-renders without putting the mutable node objects into state.
  const [graphVersion, setGraphVersion] = useState(0);

  // Simulation data lives in refs: the physics loop mutates positions every
  // frame, which must never trigger a React render.
  const nodesRef = useRef<SimNode[]>([]);
  const linksRef = useRef<SimLink[]>([]);
  const nodeMapRef = useRef<Map<string, SimNode>>(new Map());
  const adjacencyRef = useRef<Map<string, { id: string; type: GraphLinkType }[]>>(new Map());
  const pulseParticles = useRef<PulseParticle[]>([]);

  // Camera + interaction state kept in refs so the render loop never restarts
  // mid-drag (restarting it on every pan frame caused visible stutter).
  const panRef = useRef({ x: 0, y: 0 });
  const zoomRef = useRef(1);
  const isDraggingCanvas = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const draggedNodeId = useRef<string | null>(null);

  // Mirrors of the interactive state, read by the render loop.
  const hoveredIdRef = useRef<string | null>(null);
  const selectedIdRef = useRef<string | null>(null);
  const searchRef = useRef('');
  const filterRef = useRef<FilterId>('all');

  useEffect(() => {
    hoveredIdRef.current = hoveredId;
  }, [hoveredId]);
  useEffect(() => {
    selectedIdRef.current = selectedId;
  }, [selectedId]);
  useEffect(() => {
    searchRef.current = searchQuery;
  }, [searchQuery]);
  useEffect(() => {
    filterRef.current = activeFilter;
  }, [activeFilter]);

  // ------------------------------------------------------------------
  // Build the simulation from the real graph payload.
  // ------------------------------------------------------------------
  useEffect(() => {
    if (!graph) return;

    const canvas = canvasRef.current;
    const width = canvas?.clientWidth || 900;
    const height = canvas?.clientHeight || 580;
    const cx = width / 2;
    const cy = height / 2;

    // Rings by type keep the initial layout readable before the springs settle.
    const ringRadius: Record<GraphNodeType, number> = {
      founder: Math.min(width, height) * 0.16,
      startup: Math.min(width, height) * 0.28,
      incubator: Math.min(width, height) * 0.4,
      investor: Math.min(width, height) * 0.45,
    };

    const perTypeIndex: Record<string, number> = {};
    const perTypeCount = graph.nodes.reduce<Record<string, number>>((acc, n) => {
      acc[n.type] = (acc[n.type] || 0) + 1;
      return acc;
    }, {});

    const simNodes: SimNode[] = graph.nodes.map((n) => {
      const idx = perTypeIndex[n.type] ?? 0;
      perTypeIndex[n.type] = idx + 1;
      const count = Math.max(perTypeCount[n.type] || 1, 1);
      const angle = (idx / count) * Math.PI * 2 + seededUnit(n.id, 7) * 0.4;
      const r = ringRadius[n.type] * (0.85 + seededUnit(n.id, 13) * 0.3);

      return {
        id: n.id,
        name: n.name,
        type: n.type,
        refId: n.refId,
        sector: n.sector,
        location: n.location,
        connectionsCount: n.connections,
        // Size encodes real degree, so hubs read as hubs.
        radius: Math.min(30, 12 + Math.sqrt(n.connections) * 3.4),
        color: NODE_COLORS[n.type],
        x: cx + Math.cos(angle) * r,
        y: cy + Math.sin(angle) * r,
        vx: 0,
        vy: 0,
      };
    });

    const nodeMap = new Map(simNodes.map((n) => [n.id, n]));

    // Drop any link whose endpoints are missing rather than silently drawing
    // a line to nowhere.
    const simLinks: SimLink[] = graph.links.filter(
      (l) => nodeMap.has(l.source) && nodeMap.has(l.target)
    );

    const adjacency = new Map<string, { id: string; type: GraphLinkType }[]>();
    simLinks.forEach((l) => {
      if (!adjacency.has(l.source)) adjacency.set(l.source, []);
      if (!adjacency.has(l.target)) adjacency.set(l.target, []);
      adjacency.get(l.source)!.push({ id: l.target, type: l.type });
      adjacency.get(l.target)!.push({ id: l.source, type: l.type });
    });

    nodesRef.current = simNodes;
    linksRef.current = simLinks;
    nodeMapRef.current = nodeMap;
    adjacencyRef.current = adjacency;
    pulseParticles.current = simLinks.map((_, idx) => ({
      linkIndex: idx,
      progress: seededUnit(`${idx}`, 29),
      speed: 0.003 + seededUnit(`${idx}`, 31) * 0.005,
    }));

    setGraphVersion((v) => v + 1);
  }, [graph]);

  // Apply ?highlight=<refId> once the graph is available.
  useEffect(() => {
    const highlightId = searchParams.get('highlight');
    if (!highlightId || nodesRef.current.length === 0) return;
    const match = nodesRef.current.find((n) => n.refId === highlightId);
    if (match) setSelectedId(match.id);
  }, [searchParams, graphVersion]);

  // ------------------------------------------------------------------
  // Canvas sizing (high-DPI + container resize).
  // ------------------------------------------------------------------
  const updateCanvasBounds = useCallback(() => {
    const canvas = canvasRef.current;
    const parent = canvas?.parentElement;
    if (!canvas || !parent) return;

    const width = parent.clientWidth;
    const height = Math.max(580, parent.clientHeight);
    const dpr = window.devicePixelRatio || 1;

    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    // Setting canvas.width resets the transform, so this scale never compounds.
    canvas.getContext('2d')?.scale(dpr, dpr);
  }, []);

  useEffect(() => {
    updateCanvasBounds();
    const parent = canvasRef.current?.parentElement;
    if (!parent) return;
    // The canvas sits in a responsive grid column, so window resize alone
    // misses layout-driven size changes.
    const observer = new ResizeObserver(updateCanvasBounds);
    observer.observe(parent);
    return () => observer.disconnect();
  }, [updateCanvasBounds]);

  // ------------------------------------------------------------------
  // Physics + render loop.
  // ------------------------------------------------------------------
  useEffect(() => {
    if (nodesRef.current.length === 0) return;
    let animFrame = 0;

    const draw = () => {
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext('2d');
      if (!canvas || !ctx) {
        animFrame = requestAnimationFrame(draw);
        return;
      }

      const nodes = nodesRef.current;
      const links = linksRef.current;
      const nodeMap = nodeMapRef.current;
      const adjacency = adjacencyRef.current;

      const dpr = window.devicePixelRatio || 1;
      const width = canvas.width / dpr;
      const height = canvas.height / dpr;
      const center = { x: width / 2, y: height / 2 };

      // ---------------- physics ----------------
      const kRepulsion = 1900;
      const kAttraction = 0.03;
      const centerGravity = 0.008;
      const damping = 0.86;
      // Only near neighbours repel. A cutoff wider than half the canvas made
      // every node push every other one outward, packing them all against the
      // boundary clamp instead of letting clusters form.
      const repulsionCutoffSq = 40000;
      const dragged = draggedNodeId.current;

      for (let i = 0; i < nodes.length; i++) {
        const n1 = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const n2 = nodes[j];
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const distSq = dx * dx + dy * dy + 0.1;
          if (distSq > repulsionCutoffSq) continue;
          const dist = Math.sqrt(distSq);
          const force = kRepulsion / distSq;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          if (n1.id !== dragged) {
            n1.vx -= fx;
            n1.vy -= fy;
          }
          if (n2.id !== dragged) {
            n2.vx += fx;
            n2.vy += fy;
          }
        }
      }

      for (const link of links) {
        // Map lookup instead of Array.find: the old version was O(links x nodes)
        // on every frame, which dominated the frame budget once the graph grew.
        const s = nodeMap.get(link.source);
        const tg = nodeMap.get(link.target);
        if (!s || !tg) continue;
        const dx = tg.x - s.x;
        const dy = tg.y - s.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;
        const force = kAttraction * (dist - LINK_DISTANCE[link.type]);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        if (s.id !== dragged) {
          s.vx += fx;
          s.vy += fy;
        }
        if (tg.id !== dragged) {
          tg.vx -= fx;
          tg.vy -= fy;
        }
      }

      for (const node of nodes) {
        if (node.id === dragged) continue;
        node.vx += (center.x - node.x) * centerGravity;
        node.vy += (center.y - node.y) * centerGravity;
        // Clamp velocity so a dense hub can't fling nodes off-canvas.
        node.vx = Math.max(-18, Math.min(18, node.vx));
        node.vy = Math.max(-18, Math.min(18, node.vy));
        node.x += node.vx;
        node.y += node.vy;
        node.vx *= damping;
        node.vy *= damping;
        node.x = Math.max(node.radius + 8, Math.min(width - node.radius - 8, node.x));
        node.y = Math.max(node.radius + 8, Math.min(height - node.radius - 8, node.y));
      }

      for (const p of pulseParticles.current) {
        p.progress += p.speed;
        if (p.progress > 1) p.progress = 0;
      }

      // ---------------- highlight sets ----------------
      const filter = filterRef.current;
      const query = searchRef.current.trim().toLowerCase();
      const focusId = hoveredIdRef.current || selectedIdRef.current;

      const typeVisible = (n: SimNode) => filter === 'all' || n.type === filter;

      let activeIds: Set<string> | null = null;
      if (query) {
        activeIds = new Set(
          nodes.filter((n) => n.name.toLowerCase().includes(query)).map((n) => n.id)
        );
      } else if (focusId) {
        activeIds = new Set([focusId]);
        for (const peer of adjacency.get(focusId) || []) activeIds.add(peer.id);
      }

      const nodeAlpha = (n: SimNode) => {
        if (!typeVisible(n)) return 0.07;
        if (!activeIds) return 1;
        return activeIds.has(n.id) ? 1 : 0.12;
      };

      const linkAlpha = (l: SimLink) => {
        const s = nodeMap.get(l.source);
        const tg = nodeMap.get(l.target);
        if (!s || !tg) return 0;
        if (!typeVisible(s) && !typeVisible(tg)) return 0.04;
        if (!activeIds) return 0.55;
        return activeIds.has(l.source) && activeIds.has(l.target) ? 0.85 : 0.06;
      };

      // ---------------- draw ----------------
      const isDark = theme === 'dark';
      ctx.clearRect(0, 0, width, height);

      ctx.save();
      ctx.strokeStyle = isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.04)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let x = 0; x < width; x += 40) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
      }
      for (let y = 0; y < height; y += 40) {
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
      }
      ctx.stroke();
      ctx.restore();

      ctx.save();
      const pan = panRef.current;
      const zoom = zoomRef.current;
      ctx.translate(pan.x + width / 2, pan.y + height / 2);
      ctx.scale(zoom, zoom);
      ctx.translate(-width / 2, -height / 2);

      // A. links
      for (const link of links) {
        const s = nodeMap.get(link.source);
        const tg = nodeMap.get(link.target);
        if (!s || !tg) continue;
        const alpha = linkAlpha(link);
        if (alpha <= 0.05) continue;
        ctx.globalAlpha = alpha;
        ctx.beginPath();
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(tg.x, tg.y);
        ctx.strokeStyle = LINK_COLORS[link.type];
        ctx.lineWidth = alpha > 0.7 ? 2.2 : 1;
        ctx.stroke();
      }
      ctx.globalAlpha = 1;

      // B. flow particles, only along emphasised links
      for (const p of pulseParticles.current) {
        const link = links[p.linkIndex];
        if (!link) continue;
        if (linkAlpha(link) < 0.7) continue;
        const s = nodeMap.get(link.source);
        const tg = nodeMap.get(link.target);
        if (!s || !tg) continue;
        ctx.save();
        ctx.beginPath();
        ctx.arc(
          s.x + (tg.x - s.x) * p.progress,
          s.y + (tg.y - s.y) * p.progress,
          3,
          0,
          Math.PI * 2
        );
        ctx.fillStyle = LINK_COLORS[link.type];
        ctx.shadowColor = LINK_COLORS[link.type];
        ctx.shadowBlur = 8;
        ctx.fill();
        ctx.restore();
      }

      // C. nodes
      const selected = selectedIdRef.current;
      const hovered = hoveredIdRef.current;
      for (const node of nodes) {
        const alpha = nodeAlpha(node);
        if (alpha <= 0.07) continue;
        const isSelected = selected === node.id;
        const isHovered = hovered === node.id;

        ctx.save();
        ctx.globalAlpha = alpha;

        if (isSelected || isHovered) {
          const glow = node.radius * 2.2;
          const gradient = ctx.createRadialGradient(
            node.x,
            node.y,
            node.radius * 0.5,
            node.x,
            node.y,
            glow
          );
          gradient.addColorStop(0, node.color);
          gradient.addColorStop(1, 'transparent');
          ctx.beginPath();
          ctx.arc(node.x, node.y, glow, 0, Math.PI * 2);
          ctx.fillStyle = gradient;
          ctx.globalAlpha = isSelected ? 0.55 : 0.35;
          ctx.fill();
          ctx.globalAlpha = alpha;
        }

        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        ctx.fillStyle = node.color;
        ctx.fill();
        ctx.lineWidth = isSelected ? 3.5 : isHovered ? 2.5 : 1.5;
        ctx.strokeStyle =
          isSelected || isHovered
            ? '#ffffff'
            : isDark
            ? 'rgba(255,255,255,0.4)'
            : 'rgba(0,0,0,0.2)';
        ctx.stroke();

        const initials = node.name
          .split(/\s+/)
          .filter(Boolean)
          .map((w) => w[0])
          .join('')
          .substring(0, 2)
          .toUpperCase();
        ctx.fillStyle = '#ffffff';
        ctx.font = `bold ${Math.round(node.radius * 0.6)}px Inter, sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(initials, node.x, node.y);

        // Labels are culled at low zoom / low degree so a dense graph stays
        // readable instead of collapsing into overlapping text.
        const showLabel =
          isSelected || isHovered || zoom > 1.15 || node.connectionsCount >= 4 || !!activeIds;
        if (showLabel) {
          ctx.font =
            node.type === 'startup' ? 'bold 11px Inter, sans-serif' : '10px Inter, sans-serif';
          ctx.fillStyle = isDark ? '#ffffff' : '#18181b';
          ctx.textBaseline = 'top';
          const label = node.name.length > 26 ? `${node.name.slice(0, 25)}…` : node.name;
          ctx.fillText(label, node.x, node.y + node.radius + 5);
        }

        ctx.restore();
      }

      ctx.restore();
      animFrame = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animFrame);
  }, [graphVersion, theme]);

  // ------------------------------------------------------------------
  // Interaction
  // ------------------------------------------------------------------
  const screenToCanvasCoords = useCallback((clientX: number, clientY: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const pan = panRef.current;
    const zoom = zoomRef.current;
    return {
      x: (clientX - rect.left - (pan.x + rect.width / 2)) / zoom + rect.width / 2,
      y: (clientY - rect.top - (pan.y + rect.height / 2)) / zoom + rect.height / 2,
    };
  }, []);

  /** Return the closest node under the cursor, not merely the first in array order. */
  const nodeAt = useCallback((x: number, y: number): SimNode | null => {
    let best: SimNode | null = null;
    let bestDist = Infinity;
    for (const node of nodesRef.current) {
      if (filterRef.current !== 'all' && node.type !== filterRef.current) continue;
      const dx = x - node.x;
      const dy = y - node.y;
      const distSq = dx * dx + dy * dy;
      if (distSq < node.radius * node.radius * 1.6 && distSq < bestDist) {
        best = node;
        bestDist = distSq;
      }
    }
    return best;
  }, []);

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { x, y } = screenToCanvasCoords(e.clientX, e.clientY);
    const hit = nodeAt(x, y);
    if (hit) {
      draggedNodeId.current = hit.id;
      setSelectedId(hit.id);
    } else {
      isDraggingCanvas.current = true;
      dragStart.current = { x: e.clientX - panRef.current.x, y: e.clientY - panRef.current.y };
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { x, y } = screenToCanvasCoords(e.clientX, e.clientY);

    if (draggedNodeId.current) {
      const node = nodeMapRef.current.get(draggedNodeId.current);
      if (node) {
        node.x = x;
        node.y = y;
        node.vx = 0;
        node.vy = 0;
      }
      return;
    }

    if (isDraggingCanvas.current) {
      panRef.current = { x: e.clientX - dragStart.current.x, y: e.clientY - dragStart.current.y };
      return;
    }

    const hit = nodeAt(x, y);
    if ((hit?.id ?? null) !== hoveredId) setHoveredId(hit?.id ?? null);
  };

  const handleMouseUp = () => {
    draggedNodeId.current = null;
    isDraggingCanvas.current = false;
  };

  const handleMouseLeave = () => {
    handleMouseUp();
    setHoveredId(null);
  };

  // Wheel must be a non-passive native listener: React's synthetic wheel
  // handler is passive, so preventDefault() there is ignored and the page
  // scrolls while zooming.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.08 : 0.92;
      zoomRef.current = Math.max(0.4, Math.min(3, zoomRef.current * factor));
    };
    canvas.addEventListener('wheel', onWheel, { passive: false });
    return () => canvas.removeEventListener('wheel', onWheel);
  }, [graphVersion]);

  const resetView = () => {
    panRef.current = { x: 0, y: 0 };
    zoomRef.current = 1;
    setSelectedId(null);
    setSearchQuery('');
    setActiveFilter('all');
  };

  // ------------------------------------------------------------------
  // Derived UI data
  // ------------------------------------------------------------------
  const selectedNode = selectedId ? nodeMapRef.current.get(selectedId) ?? null : null;

  const selectedNeighbours = useMemo(() => {
    if (!selectedId) return [];
    return (adjacencyRef.current.get(selectedId) || [])
      .map((peer) => ({ node: nodeMapRef.current.get(peer.id), type: peer.type }))
      .filter((p): p is { node: SimNode; type: GraphLinkType } => Boolean(p.node))
      .sort((a, b) => b.node.connectionsCount - a.node.connectionsCount);
    // Node data is read from refs, so graphVersion is what invalidates this.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId, graphVersion]);

  const displayedCounts = useMemo(() => {
    const counts: Record<GraphNodeType, number> = {
      startup: 0,
      founder: 0,
      investor: 0,
      incubator: 0,
    };
    for (const n of nodesRef.current) counts[n.type] += 1;
    return counts;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graphVersion]);

  /**
   * Label a relationship from the selected node's point of view.
   *
   * Every edge runs actor -> startup. When the neighbour is the startup the
   * selected node is the actor, so the label is the verb; otherwise the
   * neighbour is the actor and the label is its role. Without this split an
   * incubator's own panel labelled each portfolio company "Incubator".
   */
  const relationLabel = (type: GraphLinkType, neighbour: SimNode) => {
    // 'supported' runs incubator -> founder, so its two sides are the founder
    // and the incubator rather than a startup and an actor.
    if (type === 'supported') {
      return neighbour.type === 'founder'
        ? isFr ? 'A accompagné' : 'Supported'
        : isFr ? 'Incubateur' : 'Incubator';
    }
    if (neighbour.type === 'startup') {
      if (type === 'founded') return isFr ? 'A fondé' : 'Founded';
      if (type === 'invested') return isFr ? 'A investi' : 'Invested';
      return isFr ? 'A incubé' : 'Incubated';
    }
    if (type === 'founded') return isFr ? 'Fondateur' : 'Founder';
    if (type === 'invested') return isFr ? 'Investisseur' : 'Investor';
    return isFr ? 'Incubateur' : 'Incubator';
  };

  const typeLabel = (type: GraphNodeType) => {
    if (type === 'startup') return 'Startup';
    if (type === 'founder') return isFr ? 'Fondateur' : 'Founder';
    if (type === 'investor') return isFr ? 'Investisseur' : 'Investor';
    return isFr ? 'Incubateur' : 'Incubator';
  };

  // There is no /incubators/:id route, so incubator nodes must not offer one.
  const canNavigate = (node: SimNode) => node.type !== 'incubator';

  const handleNodeClickNavigate = (node: SimNode) => {
    if (node.type === 'startup') navigate(`/startups/${node.refId}`);
    else if (node.type === 'founder') navigate(`/founders/${node.refId}`);
    else if (node.type === 'investor') navigate(`/investors/${node.refId}`);
  };

  const totals = graph?.totals;
  const displayedTotal =
    displayedCounts.startup +
    displayedCounts.founder +
    displayedCounts.investor +
    displayedCounts.incubator;

  return (
    <div className="space-y-6 pb-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-2 rounded-xl bg-orange-500/10 text-pulse-orange">
              <Network className="w-5 h-5" />
            </span>
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-pulse-orange">
              INTERACTIVE ECOSYSTEM GRAPH
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-zinc-900 dark:text-white tracking-tight">
            {isFr ? "Carte des Relations de l'Écosystème" : 'Ecosystem Relationship Visualizer'}
          </h1>
          <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 max-w-2xl mt-1">
            {isFr
              ? 'Chaque lien affiché provient d’un enregistrement vérifié : équipes fondatrices, tours de financement et programmes d’incubation.'
              : 'Every link shown comes from a verified record: founding teams, funding rounds, and incubation programmes.'}
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-bold bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 p-2.5 rounded-2xl shadow-sm">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-orange-500/10 text-pulse-orange">
            <span className="w-2.5 h-2.5 rounded-full bg-pulse-orange" />
            Startups ({displayedCounts.startup})
          </span>
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-blue-500/10 text-blue-500">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
            {isFr ? 'Fondateurs' : 'Founders'} ({displayedCounts.founder})
          </span>
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-emerald-500/10 text-emerald-500">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            {isFr ? 'Investisseurs' : 'Investors'} ({displayedCounts.investor})
          </span>
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-purple-500/10 text-purple-500">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500" />
            {isFr ? 'Incubateurs' : 'Incubators'} ({displayedCounts.incubator})
          </span>
        </div>
      </div>

      {/* Truncation notice — the API returns the densest slice, not everything. */}
      {graph?.truncated && totals && (
        <div className="flex items-start gap-2 text-[11px] text-amber-700 dark:text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-xl px-3 py-2">
          <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <span>
            {isFr
              ? `Affichage des ${displayedTotal} entités les plus connectées. L'écosystème complet compte ${totals.startups} startups, ${totals.founders} fondateurs, ${totals.investors} investisseurs et ${totals.incubators} incubateurs, pour ${totals.founded + totals.invested + totals.incubated + totals.supported} relations vérifiées.`
              : `Showing the ${displayedTotal} most connected entities. The full ecosystem holds ${totals.startups} startups, ${totals.founders} founders, ${totals.investors} investors and ${totals.incubators} incubators across ${totals.founded + totals.invested + totals.incubated + totals.supported} verified relationships.`}
          </span>
        </div>
      )}

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column */}
        <div className="space-y-4 lg:col-span-4">
          <div className="bg-white dark:bg-zinc-900 p-4 rounded-2xl border border-zinc-200 dark:border-zinc-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-extrabold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 flex items-center gap-1.5">
                <Filter className="w-3.5 h-3.5 text-pulse-orange" />
                {isFr ? 'Filtrer par catégorie' : 'Filter by category'}
              </span>
              <button
                onClick={resetView}
                className="inline-flex items-center gap-1 min-h-11 px-1 text-[11px] text-zinc-500 dark:text-zinc-400 hover:text-pulse-orange transition-colors rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
              >
                <RotateCcw className="w-3 h-3" />
                {t('seeAll')}
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {(
                [
                  { id: 'all', label: isFr ? 'Tout le réseau' : 'All Network' },
                  { id: 'startup', label: 'Startups' },
                  { id: 'founder', label: isFr ? 'Fondateurs' : 'Founders' },
                  { id: 'investor', label: isFr ? 'Investisseurs' : 'Investors' },
                  { id: 'incubator', label: isFr ? 'Incubateurs' : 'Incubators' },
                ] as { id: FilterId; label: string }[]
              ).map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveFilter(tab.id)}
                  className={`px-3 py-2 text-xs font-bold rounded-xl transition-all text-left ${
                    activeFilter === tab.id
                      ? 'bg-pulse-orange text-white shadow-sm'
                      : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="relative pt-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
              <Input
                placeholder={isFr ? 'Rechercher une entité...' : 'Search an entity...'}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 dark:bg-zinc-950 dark:border-zinc-800 dark:text-white text-xs h-10 rounded-xl"
              />
            </div>
          </div>

          {/* Details panel */}
          <div className="bg-white dark:bg-zinc-900 p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 transition-colors min-h-[260px] flex flex-col justify-between">
            {selectedNode ? (
              <div className="space-y-4 flex-1 flex flex-col">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Badge
                      className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border-none text-white"
                      style={{ backgroundColor: selectedNode.color }}
                    >
                      {typeLabel(selectedNode.type).toUpperCase()}
                    </Badge>
                    <span className="text-[10px] font-mono font-bold text-zinc-400 dark:text-zinc-500">
                      {selectedNode.connectionsCount} {isFr ? 'relation(s)' : 'connection(s)'}
                    </span>
                  </div>

                  <h3 className="text-lg font-black text-zinc-900 dark:text-white leading-tight">
                    {selectedNode.name}
                  </h3>

                  {selectedNode.sector && (
                    <span className="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400">
                      {selectedNode.type === 'founder'
                        ? selectedNode.sector
                        : `${isFr ? 'Secteur' : 'Sector'}: ${selectedNode.sector}`}
                    </span>
                  )}
                  {selectedNode.location && (
                    <span className="block text-[11px] text-zinc-500 dark:text-zinc-400">
                      {selectedNode.location}
                    </span>
                  )}
                </div>

                {/* The actual verified relationships for this node. */}
                <div className="flex-1">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
                    {isFr ? 'Relations vérifiées' : 'Verified relationships'}
                  </span>
                  {selectedNeighbours.length === 0 ? (
                    <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-2">
                      {isFr ? 'Aucune relation enregistrée.' : 'No recorded relationships.'}
                    </p>
                  ) : (
                    <ul className="mt-2 space-y-1 max-h-44 overflow-y-auto pr-1">
                      {selectedNeighbours.map(({ node, type }) => (
                        <li key={node.id}>
                          <button
                            onClick={() => setSelectedId(node.id)}
                            className="w-full flex items-center gap-2 text-left px-2 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                          >
                            <span
                              className="w-2 h-2 rounded-full shrink-0"
                              style={{ backgroundColor: node.color }}
                            />
                            <span className="text-[11px] font-semibold text-zinc-800 dark:text-zinc-200 truncate flex-1">
                              {node.name}
                            </span>
                            <span className="text-[9px] font-bold uppercase text-zinc-400 dark:text-zinc-500 shrink-0">
                              {relationLabel(type, node)}
                            </span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {canNavigate(selectedNode) && (
                  <Button
                    onClick={() => handleNodeClickNavigate(selectedNode)}
                    className="w-full text-xs h-10 bg-pulse-orange hover:bg-pulse-orange-hover text-white font-bold rounded-xl flex items-center justify-center gap-1.5 mt-2"
                  >
                    {isFr ? 'Voir la fiche complète' : 'View full profile'}
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                )}
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center text-xs text-zinc-500 dark:text-zinc-400 py-8 space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-orange-500/10 text-pulse-orange flex items-center justify-center">
                  <Info className="w-6 h-6" />
                </div>
                <div className="space-y-1 max-w-xs">
                  <span className="font-bold text-zinc-900 dark:text-white block text-sm">
                    {isFr ? 'Sélectionnez un nœud' : 'Select a Node'}
                  </span>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    {isFr
                      ? 'Cliquez sur une entité du graphe pour inspecter ses relations réelles.'
                      : 'Click any entity in the network graph to inspect its real relationships.'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Canvas */}
        <div className="lg:col-span-8 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl relative overflow-hidden shadow-xl min-h-[580px] flex flex-col">
          <div className="absolute top-4 left-4 z-10 flex flex-col gap-1.5 p-1.5 bg-white/90 dark:bg-zinc-950/90 backdrop-blur-md border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-lg">
            <button
              onClick={() => {
                zoomRef.current = Math.min(3, zoomRef.current * 1.15);
              }}
              className="inline-flex items-center justify-center min-w-11 min-h-11 p-2 text-zinc-700 dark:text-zinc-300 hover:text-pulse-orange transition-colors rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
              aria-label={isFr ? 'Zoom avant' : 'Zoom in'}
              title="Zoom +"
            >
              <ZoomIn className="w-4 h-4" aria-hidden="true" />
            </button>
            <button
              onClick={() => {
                zoomRef.current = Math.max(0.4, zoomRef.current * 0.85);
              }}
              className="inline-flex items-center justify-center min-w-11 min-h-11 p-2 text-zinc-700 dark:text-zinc-300 hover:text-pulse-orange transition-colors rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
              aria-label={isFr ? 'Zoom arrière' : 'Zoom out'}
              title="Zoom -"
            >
              <ZoomOut className="w-4 h-4" aria-hidden="true" />
            </button>
            <div className="w-full h-[1px] bg-zinc-200 dark:bg-zinc-800 my-0.5" />
            <button
              onClick={resetView}
              className="inline-flex items-center justify-center min-w-11 min-h-11 p-2 text-zinc-700 dark:text-zinc-300 hover:text-pulse-orange transition-colors rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
              aria-label={isFr ? 'Réinitialiser la vue' : 'Reset view'}
              title="Reset view"
            >
              <RotateCcw className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>

          {/* Relationship-type legend */}
          <div className="absolute top-4 right-4 z-10 bg-white/90 dark:bg-zinc-950/90 backdrop-blur-md border border-zinc-200 dark:border-zinc-800 px-3 py-1.5 rounded-full text-[10px] text-zinc-500 dark:text-zinc-400 font-semibold flex items-center gap-2.5 shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-pulse-orange" />
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 rounded" style={{ backgroundColor: LINK_COLORS.founded }} />
              {isFr ? 'A fondé' : 'Founded'}
            </span>
            <span className="flex items-center gap-1">
              <span
                className="w-3 h-0.5 rounded"
                style={{ backgroundColor: LINK_COLORS.invested }}
              />
              {isFr ? 'A investi' : 'Invested'}
            </span>
            <span className="flex items-center gap-1">
              <span
                className="w-3 h-0.5 rounded"
                style={{ backgroundColor: LINK_COLORS.incubated }}
              />
              {isFr ? 'A incubé' : 'Incubated'}
            </span>
            <span className="flex items-center gap-1">
              <span
                className="w-3 h-0.5 rounded"
                style={{ backgroundColor: LINK_COLORS.supported }}
              />
              {isFr ? 'A accompagné' : 'Supported'}
            </span>
          </div>

          <div className="flex-1 w-full h-full relative min-h-[580px]">
            {isLoading && (
              <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-4 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm">
                <div className="flex items-center gap-2">
                  <Skeleton className="w-10 h-10 rounded-full" />
                  <div className="space-y-2">
                    <Skeleton className="w-32 h-3 rounded" />
                    <Skeleton className="w-24 h-3 rounded" />
                  </div>
                </div>
                <span className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">
                  {isFr ? 'Chargement du graphe...' : 'Loading graph...'}
                </span>
              </div>
            )}

            {!isLoading && error && (
              <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-2 text-center px-6">
                <AlertTriangle className="w-8 h-8 text-amber-500" />
                <span className="text-sm font-bold text-zinc-900 dark:text-white">
                  {isFr ? 'Impossible de charger le graphe' : 'Could not load the graph'}
                </span>
                <span className="text-xs text-zinc-500 dark:text-zinc-400">{error.message}</span>
              </div>
            )}

            {!isLoading && !error && graph && graph.nodes.length === 0 && (
              <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-2 text-center px-6">
                <Network className="w-8 h-8 text-zinc-400" />
                <span className="text-sm font-bold text-zinc-900 dark:text-white">
                  {isFr ? 'Aucune relation enregistrée' : 'No recorded relationships'}
                </span>
              </div>
            )}

            <canvas
              ref={canvasRef}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseLeave}
              className="w-full h-full block cursor-grab active:cursor-grabbing touch-none"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
