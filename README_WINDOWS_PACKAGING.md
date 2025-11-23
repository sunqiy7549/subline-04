# Windows Packaging Guide

This guide explains how to package the News Aggregator application for Windows deployment.

## Prerequisites

1.  **Python 3.8+**: Download and install from [python.org](https://www.python.org/downloads/).
    *   **Important**: Check "Add Python to PATH" during installation.

## How to Build

We have provided a `build_windows.bat` script to automate the process.

1.  Open the project folder in File Explorer.
2.  Double-click `build_windows.bat`.
3.  Wait for the process to complete.
4.  The final executable will be generated in the `dist` folder as `NewsAggregator.exe`.

## Deployment

To deploy on another Windows PC:

1.  Copy the `NewsAggregator.exe` file.
2.  **Note on Playwright**: This application uses Playwright for web scraping. The packaged executable contains the Playwright engine, but **NOT** the browser binaries (Chromium) by default, as they are very large.
    *   **Option A (Recommended)**: On the target machine, if it has internet access, the app *should* attempt to download browsers if missing (depending on configuration), or you may need to run `playwright install chromium` if you have Python installed.
    *   **Option B (Portable)**: If you need a completely offline portable package, you need to copy the local browser cache (usually in `%USERPROFILE%\AppData\Local\ms-playwright`) to the target machine, or modify the build to include the browser binaries (advanced).

## Running the App

Double-click `NewsAggregator.exe`. A console window will open showing the logs, and the server will start (usually at `http://127.0.0.1:5001`).

## Troubleshooting

*   **Console closes immediately**: Open a command prompt (`cmd`), drag the exe into it, and press Enter to see the error message.
*   **Playwright Error**: If you see errors related to "Executable doesn't exist", it means the Chromium browser is missing.
