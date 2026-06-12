# Digital Declutter

![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Issues](https://img.shields.io/github/issues/yras279/digital-declutter)

> Seamlessly track and manage all your online subscriptions in one place. Stay organized, save money, and never lose track of recurring charges again.

---

## Table of Contents

- [About](#about)  
- [Features](#features)  
- [Getting Started](#getting-started)  
- [Prerequisites](#prerequisites)  
- [Installation](#installation)  
- [Configuration](#configuration)  
- [Usage](#usage)  
- [Data Files](#data-files)  
- [Contributing](#contributing)  
- [License](#license)  
- [Contact](#contact)

---

## About

Digital Declutter is a lightweight Python-based tool designed to help you **track and manage all your subscriptions**.  
Instead of losing money on forgotten renewals, this app keeps everything organized in one place.

---

## Features

- Add, remove, and list subscriptions  
- Store subscription details: **name, cost, billing period, due date** 
- Data stored locally in JSON (no cloud, no leaks)  
- Export data easily  
- Lightweight and easy to run anywhere  

---

## Getting Started

### Prerequisites

- Python **3.7+**  
- pip (Python package manager)  

### Installation

1. Clone the repo:

   ```bash
   git clone https://github.com/yras279/digital-declutter.git
   cd digital-declutter
   ```

2. (Optional) Create & activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   > If no `requirements.txt` exists, this is a pure Python project with no extra dependencies.

### Configuration

- **`credentials.json`** → stores API keys or credentials (if needed)  
- **`subscriptions.json`** → stores your subscription records  

###  Usage

Run the main script:

```bash
python main.py
```

Then follow the prompts to:

- Add a subscription  
- View all subscriptions  
- Delete or update existing records  

---

## Data Files

| File                  | Purpose                                                     |
|-----------------------|-------------------------------------------------------------|
| `subscriptions.json`  | Stores all subscription records (name, cost, period, date)  |
| `credentials.json`    | Stores API keys or credentials (optional use)               |

---

## Contributing

Contributions are welcome! 🎉  

1. Fork the repo  
2. Create your feature branch (`git checkout -b feature-name`)  
3. Commit changes (`git commit -m "Added new feature"`)  
4. Push branch (`git push origin feature-name`)  
5. Open a Pull Request  

Please follow **PEP 8** style guidelines and include tests where relevant.

---

## License

This project is licensed under the **MIT License**.  
See the [LICENSE](LICENSE) file for details.

---

## Contact

Author: **yras279**  
GitHub: [github.com/yras279](https://github.com/yras279)  
Email: *yras279@gmail.com*  

---

If you found this project helpful, consider giving it a star!
