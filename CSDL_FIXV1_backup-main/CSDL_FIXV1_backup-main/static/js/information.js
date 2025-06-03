async function fetchStocks() {
    try {
      const res = await fetch('/api/stocks');
      if (!res.ok) throw new Error(`Failed to fetch stocks: ${res.statusText}`);
      const data = await res.json();
      const select = document.getElementById('stock');
      select.innerHTML = '<option value="">Chọn mã cổ phiếu</option>';
      data.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.symbol;
        opt.text = d.symbol;
        select.appendChild(opt);
      }); 
      select.value = 'VCB'; // Giá trị mặc định
    } catch (error) {
      console.error('Error fetching stocks:', error);
      document.getElementById('data-table').innerHTML = '<p style="color:red;">Lỗi khi tải danh sách cổ phiếu</p>';
    }
  }

  async function fetchReportTypes() {
    try {
      const res = await fetch('/api/report_types');
      if (!res.ok) throw new Error(`Failed to fetch report types: ${res.statusText}`);
      const data = await res.json();
      const select = document.getElementById('report');
      select.innerHTML = '<option value="">Chọn loại báo cáo</option>';
      data.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.report_type_id;
        opt.text = d.report_type_name || `Loại ${d.report_type_id}: ${d.report_type}`;
        select.appendChild(opt);
      });
      select.value = '1'; // Mặc định balance_sheet
    } catch (error) {
      console.error('Error fetching report types:', error);
      document.getElementById('data-table').innerHTML = '<p style="color:red;">Lỗi khi tải danh sách loại báo cáo</p>';
    }
  }
  
  async function fetchLineItems() {
    try {
      const reportType = document.getElementById('report').value;
      if (!reportType) return;
      const res = await fetch(`/api/line_items?report_type_id=${reportType}`);
      if (!res.ok) throw new Error(`Failed to fetch line items: ${res.statusText}`);
      const data = await res.json();
      const select = document.getElementById('line');
      select.innerHTML = '<option value="">Chọn chỉ tiêu</option>';
      data.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.line_item_name;
        opt.text = d.line_item_name;
        select.appendChild(opt);
      });
    } catch (error) {
      console.error('Error fetching line items:', error);
      document.getElementById('data-table').innerHTML = '<p style="color:red;">Lỗi khi tải danh sách chỉ tiêu</p>';
    }
  }
  
  async function fetchFinancialData() {
    try {
      const stock = document.getElementById('stock').value;
      const report = document.getElementById('report').value;
      const period = document.getElementById('period').value;
      if (!stock || !report || !period) {
        document.getElementById('data-table').innerHTML = '<p style="color:red;">Vui lòng chọn đầy đủ mã cổ phiếu, loại báo cáo và khoảng thời gian</p>';
        return null;
      }
      const res = await fetch(`/api/financial_data?symbol=${stock}&report_type_id=${report}&period=${period}`);
      if (!res.ok) throw new Error(`Failed to fetch financial data: ${res.statusText}`);
      const data = await res.json();
      renderTable(data, period);
      return data;
    } catch (error) {
      console.error('Error fetching financial data:', error);
      document.getElementById('data-table').innerHTML = `<p style="color:red;">Lỗi khi tải dữ liệu tài chính: ${error.message}</p>`;
      return null;
    }
  }
  
  function renderTable(data, period) {
    const container = document.getElementById('data-table');
    if (data.error) {
      container.innerHTML = `<p style="color:red;">${data.error}</p>`;
      return;
    }
    if (!Array.isArray(data) || data.length === 0) {
      container.innerHTML = '<p style="color:red;">Không có dữ liệu để hiển thị</p>';
      return;
    }
    let html = '<table><tr><th>Chỉ tiêu</th>';
    if (period === 'yearly') {
      for (let y = 2020; y <= 2024; y++) {
        html += `<th>${y}</th>`;
      }
    } else {
      for (let y = 2020; y <= 2024; y++) {
        for (let q = 1; q <= 4; q++) {
          html += `<th>${y} Q${q}</th>`;
        }
      }
    }
    html += '</tr>';
    data.forEach(row => {
      html += `<tr><td>${row.item}</td>`;
      if (period === 'yearly') {
        for (let y = 2020; y <= 2024; y++) {
          html += `<td>${row[y] !== null && row[y] !== undefined ? row[y] : '-'}</td>`;
        }
      } else {
        for (let y = 2020; y <= 2024; y++) {
          for (let q = 1; q <= 4; q++) {
            const key = `${y}Q${q}`;
            html += `<td>${row[key] !== null && row[key] !== undefined ? row[key] : '-'}</td>`;
          }
        }
      }
      html += '</tr>';
    });
    html += '</table>';
    container.innerHTML = html;
  }
  
  async function drawChart() {
    try {
      const lineItem = document.getElementById('line').value;
      const period = document.getElementById('period').value;
      if (!lineItem) {
        alert('Vui lòng chọn chỉ tiêu để vẽ biểu đồ!');
        return;
      }
      const data = await fetchFinancialData();
      if (!data || data.error || !Array.isArray(data)) {
        alert('Không có dữ liệu để vẽ biểu đồ!');
        return;
      }
      const item = data.find(row => row.item === lineItem);
      if (!item) {
        alert('Không có dữ liệu cho chỉ tiêu này!');
        return;
      }
  
      let labels;
      if (period === 'yearly') {
        labels = Object.keys(item).filter(k => k.match(/^\d{4}$/)).sort();
      } else {
        labels = Object.keys(item).filter(k => k.match(/^\d{4}Q[1-4]$/)).sort();
      }
      const values = labels.map(y => item[y]);
  
      const ctx = document.getElementById('chartCanvas').getContext('2d');
      if (window.chart) window.chart.destroy();
      window.chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [{
            label: lineItem,
            data: values,
            borderColor: 'blue',
            fill: false
          }]
        },
        options: {
          responsive: true,
          scales: {
            y: { beginAtZero: false }
          }
        }
      });
  
      document.getElementById('overlay').style.display = 'block';
      document.getElementById('chartModal').style.display = 'block';
    } catch (error) {
      console.error('Error drawing chart:', error);
      alert('Lỗi khi vẽ biểu đồ.');
    }
  }
  
  function closeChart() {
    document.getElementById('overlay').style.display = 'none';
    document.getElementById('chartModal').style.display = 'none';
  }
  
  // Gắn sự kiện thay đổi
  document.getElementById('report').addEventListener('change', async () => {
    await fetchLineItems();
    await fetchFinancialData();
  });
  
  document.getElementById('stock').addEventListener('change', fetchFinancialData);
  
  document.getElementById('period').addEventListener('change', fetchFinancialData);
  
  // Khởi tạo khi trang tải
  window.onload = async () => {
    await Promise.all([fetchStocks(), fetchReportTypes()]);
    await fetchLineItems();
    await fetchFinancialData();
  };