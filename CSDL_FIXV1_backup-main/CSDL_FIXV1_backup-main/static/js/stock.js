async function updateStock() {
    const symbol = document.getElementById('symbol').value;
    try {
        const response = await fetch(`/api/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({ symbol: symbol })
        });
        if (!response.ok) {
            throw new Error('Error loading stock data');
        }

        const pageContent = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(pageContent, 'text/html');

        // Update stock info
        const newStockInfo = doc.querySelector('.stock-info');
        if (newStockInfo) {
            const currentStockInfo = document.querySelector('.stock-info');
            currentStockInfo.innerHTML = newStockInfo.innerHTML;
        }

        // Update real-time data
        const newRealtimeTable = doc.querySelector('.realtime-table');
        if (newRealtimeTable) {
            const currentRealtimeTable = document.querySelector('.realtime-table');
            currentRealtimeTable.innerHTML = newRealtimeTable.innerHTML;
        }

        // Update history data
        const newHistoryTable = doc.querySelector('.history-table');
        if (newHistoryTable) {
            const currentHistoryTable = document.querySelector('.history-table');
            currentHistoryTable.innerHTML = newHistoryTable.innerHTML;
        }

        // Update chart
        const newChart = doc.querySelector('.chart');
        if (newChart) {
            const currentChart = document.querySelector('.chart');
            currentChart.innerHTML = newChart.innerHTML;
        }

    } catch (error) {
        console.error('Error loading stock data:', error);
    }
}