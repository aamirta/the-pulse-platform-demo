# Launch email — "I'm in The Pulse" badge

Sent to the ~12 top founders whose startups are most visible (YoLa Fresh,
Freterium, Chari, Mubawab, Kifal, ORA, etc.). Their badge is already
pre-generated in `samples/`.

## Subject lines to A/B test

- `Ton badge officiel de l'écosystème startup marocain est prêt`
- `🇲🇦 Ton visage sur la carte du Pulse`
- `[prénom], j'ai fait quelque chose pour toi`

## Body (FR)

---

Salut [Prénom],

On a cartographié l'écosystème startup marocain pour la première fois :
**1 951 startups**, **1 155 founders**, **45 incubateurs**, $226M levés.

Et **tu y es**. Ton profil fait partie des plus visibles de la plateforme —
on a préparé ton badge officiel :

[IMAGE en pièce jointe : badge_<prenom>.png]

**3 clics :**

1. Télécharge l'image ci-dessus
2. Copie-colle la légende plus bas
3. Poste sur LinkedIn → ton réseau découvre The Pulse

---

### Légende prête à coller

```
I'm in The Pulse 🇲🇦
Morocco's startup ecosystem, mapped.
Join me!
https://thepulse.ma/badge?ref=<member_id>
```

---

Chaque personne qui te rejoint via ton lien s'attribue à ton profil — on
saura qui construit l'écosystème avec nous.

Et si tu veux refaire ton badge (photo différente, rôle différent, catégorie
différente) → https://thepulse.ma/badge → tout est auto-rempli.

Merci de faire partie du Pulse,
[Signature]

---

## Target list (à personnaliser)

Les badges sont dans `marketing/badge_demo/samples/` :

| Founder          | Startup     | Badge file         | Email |
|------------------|-------------|--------------------|-------|
| Larbi Belrhiti   | YoLa Fresh  | badge_01_larbi.png | (à récupérer) |
| Youssef Mamou    | YoLa Fresh  | badge_02_mamou.png | |
| Ismail Belkhayat | Chari       | badge_03_ismail.png| |
| Mehdi Alami      | Freterium   | badge_04_mehdi.png | |
| Hamid Bouchikhi  | UM6P Expert | badge_05_hamid.png | hamid.bouchikhi@um6p.ma |
| Simohammed Damiri| Nessiam     | badge_06_simo.png  | simohammed.damiri@gmail.com |
| Omar Alami       | ORA         | badge_07_omar.png  | |
| Tarik Haddi      | AMIC        | badge_08_tarik.png | |

## Next founders to generate

- Sophia Alj (Chari)
- Kevin Gormand (Mubawab)
- Omar Kouhene (Freterium)
- Moncef Chlouchi
- Ayman Touhami
- Amine Raji

To batch-generate:

```bash
cd marketing/badge_demo
python3 batch_generate.py   # edit the PLAN list first
```
