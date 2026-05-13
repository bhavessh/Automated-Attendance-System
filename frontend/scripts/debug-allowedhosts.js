// Debug script: inspect webpackDevServer.config allowedHosts
const cfg = require('../node_modules/react-scripts/config/webpackDevServer.config.js');
const result = cfg({}, '');
console.log('allowedHosts:', result.allowedHosts);
console.log('type:', typeof result.allowedHosts);
if (Array.isArray(result.allowedHosts)) {
  console.log('array length:', result.allowedHosts.length);
  console.log('first element:', JSON.stringify(result.allowedHosts[0]));
}
