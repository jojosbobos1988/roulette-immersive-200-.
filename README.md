
# Immersive Roulette — Last 200 + Missing (Codespaces)

Αυτό το πακέτο τραβάει τα **τελευταία 200 spins** από το CasinoScores (Immersive Roulette) και βγάζει **ποιες τιμές 0–36 δεν εμφανίστηκαν**.

## Βήμα-βήμα (iPhone/Safari με GitHub Codespaces)
1) Πήγαινε στο **github.com** → **Sign in** → **+ → New repository** → φτιάξε repo (π.χ. `roulette-immersive-200`).
2) Στο repo: **Add file → Upload files** → ανέβασε **όλο** το zip (ή κάνε unzip και ανέβασε τα αρχεία).
3) Πάτα **Code → Codespaces → Create codespace on main** και περίμενε να ανοίξει το VS Code στο browser.
4) Αν δεν βλέπεις όλα τα panels, στον Safari πάτα **aA → Request Desktop Website**.
5) Τρέξε τον scraper:
   - **Terminal** → εκτέλεσε:
     ```bash
     python3 scrape_immersive_last200_missing.py --csv immersive_last200.csv --missing-csv missing_numbers.csv --missing-json missing_numbers.json --print
     ```
     ή
   - **Terminal → Run Task → Run scraper (200 + missing)**

6) Αρχεία εξόδου (στην αριστερή στήλη/Explorer):
   - `immersive_last200.csv` → όλα τα spins (αριθμός/χρώμα/timestamp/source)
   - `missing_numbers.csv` → μία στήλη με τους αριθμούς που **δεν** εμφανίστηκαν (0..36)
   - `missing_numbers.json` → JSON με `missing_numbers`, `count`, `captured_at`

## Παραμετροποίηση
- Μέγιστο spins: `--max 200` (π.χ. βάλε `--max 150`).
- Χρόνος αναμονής φόρτωσης: `--wait 25` (αν αργεί, δοκίμασε `--wait 40`).

## Συχνές λύσεις
- Αν πάρεις λίγα/κενά αποτελέσματα, ξανατρέξε την εντολή (η σελίδα φορτώνει δυναμικά).
- Αν αλλάξει η δομή του site, ζήτησε μου να ενημερώσω selectors ή να περάσουμε σε JSON feed (χωρίς Selenium).
