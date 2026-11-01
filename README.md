# Shopora — Amazon-inspired Docker storefront

## Windows setup
1. Install Docker Desktop, start it and enable the Linux container engine.
2. Extract the ZIP into a normal folder.
3. Double-click **start.bat** (or run `docker compose up -d --build`).
4. Open **http://localhost:8080**.
5. Use **stop.bat** to stop the application; **logs.bat** for logs.

## Default admin account
- Email: `admin@shopora.local`
- Password: `ChangeMe123!`

**IMPORTANT:** Change `ADMIN_PASSWORD` inside `.env` BEFORE first boot. The admin account is seeded only if it doesn't exist; after first boot, changing `.env` does not update an existing admin password. Do not expose this demo publicly without adding a password reset workflow, HTTPS, email verification, security hardening and rate limiting.

## Features
- Responsive shopping storefront, product grid, categories, featured deals, text search, sorting and product detail modal
- Cart and checkout, user registration/login, order history
- Admin dashboard, product creation/editing/deleting, inventory, order status changes
- SQLite database retained in named Docker volume `shopora_data`
- Demo images loaded from Unsplash (Internet connection required for product photos)

## Limitations
- This is an original Amazon-inspired demonstration, not Amazon code/branding.
- Only **Cash on Delivery** (demo order placement) is implemented. Payment gateway, tax/GST, shipping rates, SMS OTP, real payments, reviews and email notifications need integration before a production launch.
- Prices are sample INR prices. Products are fictitious seeded listings, not live Amazon products.
- Use `docker compose down -v` only if you intend to DELETE the database and all orders.
