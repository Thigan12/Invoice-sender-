# Invoice Sender Pro 🚀

A sleek, modern, and professional desktop application designed to streamline the invoicing process for small to medium-sized businesses. This tool automates everything from Excel data ingestion to PDF generation and WhatsApp delivery.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![PySide6](https://img.shields.io/badge/UI-PySide6-green.svg)

## ✨ Key Features

- **📊 Dynamic Dashboard:** Get a bird's-eye view of your recent imports, customer counts, and total invoice values.
- **📁 Smart Excel Import:** Directly import invoice details from Excel files. The app intelligently maps column headers and handles missing data.
- **📋 Clipboard Integration:** Copy data from Excel and paste it directly into the app—no need to save files every time!
- **📄 Professional PDF Engine:** Generates beautiful, high-quality PDF invoices automatically with custom branding and a dedicated "Delivery Fee" logic.
- **📱 WhatsApp Automation:** One-click "Send" opens the customer's WhatsApp chat, copies the PDF to your clipboard, and can even automate the paste-and-send action (via PyAutoGUI).
- **🕵️ Fuzzy Matching:** Built-in intelligence to recognize customers even if their names are spelled slightly differently across different imports.
- **🗄️ Robust Database:** Uses SQLite to store customer history, products, and generated invoice records locally and securely.

## 🛠️ Tech Stack

- **GUI Framework:** [PySide6](https://doc.qt.io/qtforpython/) (Qt for Python)
- **Data Processing:** [Pandas](https://pandas.pydata.org/)
- **PDF Generation:** [ReportLab](https://www.reportlab.com/)
- **Database:** SQLite
- **Automation:** [PyAutoGUI](https://pyautogui.readthedocs.io/)
- **Matching Engine:** [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz)

## 🚀 Getting Started

### Prerequisites

- **Python 3.8 or higher**
- **Git**

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Thigan12/Invoice-sender-.git
   cd Invoice-sender-
   ```

2. **Create a virtual environment (Recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

```bash
python src/main.py
```

## 📖 How to Use

1. **Import Data:** Navigate to the **Import** page. You can either select an Excel file or use the "Paste from Excel" feature.
2. **Review Invoices:** Check the data in the preview table. Once imported, invoices will appear in the **Invoices** section.
3. **Manage Customers:** Select a customer from the sidebar to see their specific items.
4. **Generate & Send:** 
   - Click **Generate PDF** to create the invoice file.
   - Click **Send WhatsApp** to open a chat. The PDF is automatically copied for you—just paste it in the chat!

## 📂 Project Structure

```text
Invoice sender/
├── src/
│   ├── core/         # Business logic (PDF engine, WhatsApp bridge, Data processing)
│   ├── database/     # DB connection and Repository patterns
│   ├── ui/           # PySide6 views, widgets, and styles
│   ├── utils/        # Spreadsheet parsers and helper functions
│   └── main.py       # Application entry point
├── data/             # SQLite database and generated PDFs (local only)
├── assets/           # UI icons and branding assets
└── README.md
```

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

---

**Developed with ❤️ by [Thigan](https://github.com/Thigan12)**
