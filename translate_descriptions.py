"""
Translate all startup descriptions from French to English.
Adds description_en column to Startup table and populates it.
"""
import sys
import time
from deep_translator import GoogleTranslator
from app import app, db
from models import Startup

translator = GoogleTranslator(source='fr', target='en')

def translate_batch():
    with app.app_context():
        # Check if description_en column exists, add if not
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('Startups')]
        if 'description_en' not in columns:
            db.session.execute(text('ALTER TABLE Startups ADD COLUMN description_en TEXT'))
            db.session.commit()
            print("Added description_en column")

        startups = Startup.query.filter(Startup.description.isnot(None)).filter(Startup.description != '').all()
        total = len(startups)
        print(f"Found {total} startups with descriptions to translate")

        translated = 0
        failed = 0

        for i, s in enumerate(startups):
            # Skip if already translated
            if hasattr(s, 'description_en') and s.description_en and len(s.description_en) > 5:
                translated += 1
                continue

            desc = s.description.strip()
            if not desc or len(desc) < 3:
                continue

            try:
                # Truncate very long descriptions
                if len(desc) > 4000:
                    desc = desc[:4000]

                en_text = translator.translate(desc)
                s.description_en = en_text
                translated += 1

                # Commit every 20 translations
                if translated % 20 == 0:
                    db.session.commit()
                    print(f"  Progress: {translated}/{total} ({i+1} processed, {failed} failed)")

                # Small delay to avoid rate limiting
                time.sleep(0.1)

            except Exception as e:
                failed += 1
                s.description_en = desc  # Keep original if translation fails
                if failed % 10 == 0:
                    print(f"  Failed {failed} translations. Last error: {e}")
                time.sleep(0.5)

        db.session.commit()
        print(f"\nDone! Translated: {translated}, Failed: {failed}, Total: {total}")

if __name__ == '__main__':
    translate_batch()
