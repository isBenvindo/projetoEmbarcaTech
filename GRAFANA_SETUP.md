# Grafana Setup Guide

This guide explains how to connect Grafana to the Terelina project's PostgreSQL database to enable data visualization.

It assumes you have a running Grafana instance and that the project's backend (with the PostgreSQL database) is also running.

---

## 1. Accessing Grafana

By default, Grafana is available at `http://localhost:3000`.

- **Default Username:** `admin`
- **Default Password:** `admin`

You will be prompted to change the password on your first login.

---

## 2. Configuring the PostgreSQL Data Source

To allow Grafana to read data from the project's database, you must configure a new data source.

1.  From the Grafana side menu, navigate to **Connections** > **Data Sources**.
2.  Click the **"Add new data source"** button.
3.  Search for and select **"PostgreSQL"**.

4.  Fill in the connection form with the following details:

    - **Name:** `Terelina PostgreSQL` (or any name you prefer)
    - **Host:** `localhost:5432`
      - *Note: If your Grafana is running inside a Docker container on the same network as the project, use `db:5432` instead.*
    - **Database:** `terelina_db`
    - **User:** `postgres`
    - **Password:** `postgres`
      - *Note: These are the default credentials from the project's `docker-compose.yml` file.*
    - **TLS/SSL Mode:** `disable`
    - **PostgreSQL Version:** Leave as default or select `15`.

5.  Click the **"Save & test"** button at the bottom. You should see a green checkmark with the message "Database Connection OK".

---

## 3. Creating Dashboards

With the data source configured, you are now ready to create dashboards and panels.

1.  Navigate to **Dashboards** from the side menu.
2.  Create a **New Folder** named "Terelina" to keep your dashboards organized.
3.  Inside the folder, create a **New Dashboard**.
4.  For each panel, select the `Terelina PostgreSQL` data source and use the query editor in **"Code"** mode to write your SQL queries.

**Tip:** Start by testing a simple query to ensure everything is working:
```sql
SELECT
  date AS "time",
  total_counts
FROM daily_counts
WHERE $__timeFilter(date)
ORDER BY 1;
```

This query uses the optimized daily_counts view and will display the total production for each day in the selected time range.

---

## 4. Troubleshooting

**Problem: "Database Connection OK" fails**

- **Verify Backend is Running:** Ensure the project's Docker containers are running by executing `docker ps`. You should see `terelina_db` in the list.
- **Check Host Address:** If Grafana and Docker are on different machines, replace `localhost` with the correct IP address of the machine running the Docker containers.
- **Check Credentials:** Double-check that the database name, user, and password match the values in the `docker-compose.yml` or your `.env` file.

**Problem: Panels show "No data"**

- **Populate the Database:** The database is empty by default. Make sure you have run the data population script as described in `INSTALLATION.md`.
- **Check Time Range:** Ensure the time range selected in the top-right corner of your Grafana dashboard (e.g., "Last 1 year") covers the period for which you have generated data.
- **Test the Query:** Use a database client or the `docker exec` command to connect to the database and run your SQL query directly. This helps confirm if the query itself is correct.
  ```bash
  # Using docker-compose (preferred):
  docker-compose exec -T db psql -U postgres -d terelina_db

  # Or using the container name directly:
  docker exec -it terelina_db psql -U postgres -d terelina_db
  ```

---

## Security Note

- This project uses default credentials for local development (Postgres: `postgres/postgres`, Grafana: `admin/admin`). These are for local testing only — change them before exposing services or using in non-local environments.
