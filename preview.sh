#!/bin/bash
# Preview Queue Monitor Coming Soon page

echo "Opening Queue Monitor Coming Soon page in browser..."
python3 -m http.server 8080 --directory /home/zzy/auto-company/projects/queue-monitor &
echo "Server started at http://localhost:8080/coming-soon.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "Alternatively, open the file directly:"
echo "file:///home/zzy/auto-company/projects/queue-monitor/coming-soon.html"
