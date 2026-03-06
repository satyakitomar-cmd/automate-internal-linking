const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = 4173;
const DIST = path.join(__dirname, "dist");

const MIME = {
  ".html": "text/html",
  ".js": "application/javascript",
  ".css": "text/css",
  ".svg": "image/svg+xml",
  ".json": "application/json",
  ".png": "image/png",
  ".ico": "image/x-icon",
};

http.createServer((req, res) => {
  let filePath = path.join(DIST, req.url === "/" ? "index.html" : req.url);
  if (!fs.existsSync(filePath)) filePath = path.join(DIST, "index.html");
  const ext = path.extname(filePath);
  res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream" });
  fs.createReadStream(filePath).pipe(res);
}).listen(PORT, () => console.log(`Listening on http://localhost:${PORT}`));
