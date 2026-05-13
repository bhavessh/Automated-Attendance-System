// Logs env vars that affect webpack-dev-server then starts CRA dev server
console.log('ENV CHECK: ALLOWED_HOSTS="' + (process.env.ALLOWED_HOSTS ?? '') + '"');
console.log('ENV CHECK: HOST="' + (process.env.HOST ?? '') + '"');
console.log('ENV CHECK: PUBLIC_URL="' + (process.env.PUBLIC_URL ?? '') + '"');
console.log('ENV CHECK: BROWSER="' + (process.env.BROWSER ?? '') + '"');
console.log('ENV CHECK: npm_package_proxy="' + (process.env.npm_package_proxy ?? '') + '"');

// Small parse for ALLOWED_HOSTS
if (process.env.ALLOWED_HOSTS !== undefined) {
  const arr = process.env.ALLOWED_HOSTS.split(',');
  console.log('Parsed ALLOWED_HOSTS ->', arr);
  const empty = arr.filter(s => typeof s === 'string' && s.trim() === '');
  if (empty.length > 0) {
    console.warn('Warning: ALLOWED_HOSTS contains empty entries:', arr);
  }
}

// Inject safe defaults if variables are missing/empty to avoid webpack-dev-server schema errors
if (!process.env.ALLOWED_HOSTS || process.env.ALLOWED_HOSTS.trim() === '') {
  process.env.ALLOWED_HOSTS = 'localhost,127.0.0.1';
  console.log('Injected default ALLOWED_HOSTS="' + process.env.ALLOWED_HOSTS + '"');
}
if (!process.env.HOST || process.env.HOST.trim() === '') {
  // Do not bind to 0.0.0.0 by default on Windows; use localhost for safety
  process.env.HOST = '127.0.0.1';
  console.log('Injected default HOST="' + process.env.HOST + '"');
}
// Disable host check so webpack-dev-server uses 'all' for allowedHosts
process.env.DANGEROUSLY_DISABLE_HOST_CHECK = 'true';
console.log('Injected DANGEROUSLY_DISABLE_HOST_CHECK=true');

// Start CRA dev server
require('react-scripts/scripts/start');
