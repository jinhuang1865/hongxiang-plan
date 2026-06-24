// Cloudflare Worker for Hongxiang Plan View Counter
// Uses KV storage for persistence

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
  "Content-Type": "application/json",
};

addEventListener("fetch", (event) => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: CORS_HEADERS });
  }

  const url = new URL(request.url);

  // GET /api/views - return all view counts
  if (request.method === "GET" && url.pathname === "/api/views") {
    try {
      const data = await VIEW_COUNTS.get("counts", { type: "json" }) || {};
      return new Response(JSON.stringify({ views: data }), { headers: CORS_HEADERS });
    } catch (e) {
      return new Response(JSON.stringify({ views: {} }), { headers: CORS_HEADERS });
    }
  }

  // POST /api/views - increment a course view count
  if (request.method === "POST" && url.pathname === "/api/views") {
    try {
      const body = await request.json();
      const courseId = body.id;
      if (!courseId) {
        return new Response(JSON.stringify({ error: "Missing id" }), { status: 400, headers: CORS_HEADERS });
      }
      const data = await VIEW_COUNTS.get("counts", { type: "json" }) || {};
      data[courseId] = (data[courseId] || 0) + 1;
      await VIEW_COUNTS.put("counts", JSON.stringify(data));
      return new Response(JSON.stringify({ success: true, count: data[courseId] }), { headers: CORS_HEADERS });
    } catch (e) {
      return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: CORS_HEADERS });
    }
  }

  // Default response
  return new Response(JSON.stringify({ hello: "hongxiang-views" }), { headers: CORS_HEADERS });
}
