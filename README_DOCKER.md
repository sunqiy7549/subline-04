# Docker Deployment Guide

This guide explains how to deploy the News Aggregator application using Docker.

## Prerequisites

-   **Docker**: Ensure Docker and Docker Compose are installed on your server or machine.

## Deployment Steps

1.  **Clone the Repository** (if not already done):
    ```bash
    git clone https://github.com/sunqiy7549/news_aggreg.git
    cd news_aggreg
    ```

2.  **Build and Run**:
    Run the following command to build the image and start the container in the background:
    ```bash
    docker-compose up -d --build
    ```

3.  **Access the Application**:
    The application will be available at `http://localhost:5001` (or your server's IP address).

## Management

-   **Stop the application**:
    ```bash
    docker-compose down
    ```

-   **View Logs**:
    ```bash
    docker-compose logs -f
    ```

-   **Update the application**:
    ```bash
    git pull
    docker-compose up -d --build
    ```

## Data Persistence

The `data` directory is mounted as a volume, so downloaded news data will persist even if the container is recreated.
