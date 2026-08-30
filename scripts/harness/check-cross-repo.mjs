#!/usr/bin/env node

import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const ROOT = process.cwd();
const feEndpointsFile = join(ROOT, "src/lib/api/endpoints.ts");
const apiRoutesFile = join(ROOT, "apps/quant-api/app/api/routes/auth.py");
const errors = [];

function read(path) {
  return existsSync(path) ? readFileSync(path, "utf8") : null;
}

const fe = read(feEndpointsFile);
const apiRoutes = read(apiRoutesFile);

if (!fe) errors.push("FE endpoints.ts missing");
if (!apiRoutes) errors.push("FastAPI auth routes missing");

if (fe && apiRoutes) {
  const feEndpoints = new Set(
    [...fe.matchAll(/"(\/api\/v1\/auth\/[a-z-/]+)"/g)].map((match) => match[1])
  );
  const apiEndpoints = new Set(
    [...apiRoutes.matchAll(/@router\.(?:post|get|delete|put|patch)\("(\/[^"?]+)"/g)].map(
      (match) => `/api/v1/auth${match[1]}`
    )
  );
  const feOnly = [...feEndpoints].filter((endpoint) => !apiEndpoints.has(endpoint));
  const apiOnly = [...apiEndpoints].filter((endpoint) => !feEndpoints.has(endpoint));

  if (feOnly.length) {
    errors.push(`Endpoints in FE but not in FastAPI routes: ${feOnly.join(", ")}`);
  }
  if (apiOnly.length) {
    errors.push(`Routes in FastAPI but not in FE endpoints: ${apiOnly.join(", ")}`);
  }
}

for (const error of errors) console.error(`✖  ${error}`);

if (errors.length > 0) {
  console.error(`\nverify:cross-repo FAILED — ${errors.length} error(s).`);
  process.exit(1);
}

console.log("verify:cross-repo OK — frontend endpoints match FastAPI routes.");
