// index.js
const { onRequest } = require("firebase-functions/v2/https");
const { runWith } = require("firebase-functions/v2/https");
const { setGlobalOptions } = require("firebase-functions/v2");
const { app } = require("./main.py");

setGlobalOptions({
    region: 'us-central1'
});

// Expose the Flask application as a single function
exports.alfurqa_academy_app = onRequest(app);
