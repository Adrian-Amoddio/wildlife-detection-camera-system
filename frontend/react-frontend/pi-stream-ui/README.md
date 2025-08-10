# Frontend

This folder contains the React website for the Wildlife Detection Camera System.  
It connects to the EC2 server to display live video and sensor data from the Raspberry Pi.

## Folder Structure

```
frontend/
└── react-frontend/
    └── pi-stream-ui/
        ├── public/
        ├── src/
        ├── package.json
        ├── package-lock.json
        ├── .env.example           # Example environment variables
        └── README.md
```

## Key Features

- Displays live HLS video from the EC2 streaming server.
- Shows temperature, pressure and humidity data from the Pi 5
- Simple, responsive UI for system control and monitoring the environement

## Setup

1. Install dependencies:

   ```bash
   npm install
   ```

2. Create an `.env` file based on `.env.example` and update it with your backend URLs and IPs.

3. Start the development server (local testing only):

   ```bash
   npm start
   ```

   This runs the app at `http://localhost:3000` for development purposes.  
   Note: In production, the frontend can be hosted on any server (including remote/cloud hosting) and accessed from anywhere. It is not limited to local network use.

4. Open `http://localhost:3000` in your browser.

## Build for Production

```bash
npm run build
```

The production build will be output to the `build/` directory and can be served via any static file server.

## License

This project is licensed under the [MIT License](../LICENSE).
