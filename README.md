# Project Helix @ Illinois 🧬

Project Helix is a modern, high-performance event discovery platform designed specifically for the University of Illinois community. By aggregating data from across campus—including dining halls, libraries, and student organizations—Helix provides a centralized hub for uncovering opportunities, with a special focus on social gatherings and "Free Food 🍕" events.

## 🚀 Key Features

-   **Dynamic Event Discovery**: Real-time scraping of campus sources to ensure the most up-to-date information.
-   **Typo-Tolerant Fuzzy Search**: Powered by [Fuse.js](https://fusejs.io/), helping you find events even with misspelled queries (e.g., "basktball" → "Basketball").
-   **Automated "Free Food 🍕" Tagging**: Smart keyword and location-based detection to highlight events with complimentary meals.
-   **Google Calendar Integration**: Seamlessly sync events directly to your personal calendar.
-   **Aesthetic Dark/Light Theme**: A premium, responsive UI optimized for both desktop and mobile viewing.
-   **Static Architecture**: Fast, lightweight, and hosted entirely on GitHub Pages.

## 🏗️ Architecture

Project Helix is built as a **static web application** that consumes a periodically updated JSON data source.

-   **Frontend**: Vanilla HTML5, CSS3 (with Glassmorphism), and Modern JavaScript.
-   **Data Engine**: A Python-based "scavenger" that scrapes campus websites and outputs a minified `scraped_events.json`.
-   **Search Engine**: Client-side fuzzy search using Fuse.js.
-   **Hosting**: Deployed directly via GitHub Pages.

## 🛠️ Getting Started

### Prerequisites

-   Python 3.10+
-   `pip` (Python package manager)

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/infoshubhjain/Project-Helix.git
    cd Project-Helix
    ```

2.  **Install dependencies**:
    ```bash
    make install
    ```

### Running Locally

Since Project Helix is a static site, you can view it by simply opening `index.html` in any modern web browser.

To update the event data locally:
```bash
make scrape-local
```

## 📜 Technical Details

-   **Languages**: HTML, CSS, JavaScript, Python
-   **Libraries**: Fuse.js (Search), BeautifulSoup4/Playwright (Scraping)
-   **Deployment**: GitHub Pages

---
*Built with ❤️ for the Illinois community.*
