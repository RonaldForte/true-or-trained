// PM2 config for LOCAL DEVELOPMENT only. Production runs on Render, not PM2.
// Usage (from repo root): pm2 start ecosystem.config.js
module.exports = {
  apps: [
    {
      name: "backend",
      cwd: "./backend",
      // Run the venv's Python directly so PM2 uses the right packages
      // without needing the venv activated in your shell.
      // pythonw = windowless Python. python.exe pops up a console window on
      // Windows because the venv launcher spawns the real interpreter unhidden.
      script: ".venv/Scripts/pythonw.exe",
      args: "-m uvicorn app.main:app --port 8000",
      interpreter: "none",
      // PM2 restarts on file changes instead of uvicorn --reload: the reload
      // worker uvicorn spawns can't write to PM2's logs under pythonw.
      watch: ["app"],
      env: {
        // Without this, Python buffers output when not attached to a terminal,
        // so logs show up late or in bursts.
        PYTHONUNBUFFERED: "1",
        // Skip writing __pycache__/*.pyc -- PM2's watcher would see those
        // files appear on startup and trigger an extra restart.
        PYTHONDONTWRITEBYTECODE: "1",
      },
      out_file: "../logs/backend.out.log",
      error_file: "../logs/backend.err.log",
      time: true,
      windowsHide: true,
    },
    {
      name: "frontend",
      cwd: "./frontend",
      // Run Vite's CLI with node directly rather than via npm.cmd, which
      // PM2 can't spawn cleanly on Windows. Vite does its own hot reload.
      script: "node_modules/vite/bin/vite.js",
      args: "--port 5173 --strictPort",
      env: {
        NO_COLOR: "1",
      },
      out_file: "../logs/frontend.out.log",
      error_file: "../logs/frontend.err.log",
      time: true,
      windowsHide: true,
    },
  ],
};
