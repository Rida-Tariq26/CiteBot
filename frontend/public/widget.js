(function () {
  const currentScript = document.currentScript || document.querySelector('script[data-deployment-id]');
  const deploymentId = currentScript?.getAttribute('data-deployment-id') || 'default';
  const apiUrl = currentScript?.getAttribute('data-api-url') || window.location.origin;

  // Create isolated container
  const host = document.createElement('div');
  host.id = 'citebot-widget-root';
  document.body.appendChild(host);

  const shadow = host.attachShadow({ mode: 'open' });

  // Styles
  const style = document.createElement('style');
  style.textContent = `
    * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .btn-launcher {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 56px;
      height: 56px;
      border-radius: 28px;
      background: #2563EB;
      color: white;
      border: none;
      box-shadow: 0 4px 14px rgba(37,99,235,0.4);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 999999;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .btn-launcher:hover { transform: scale(1.05); }
    .widget-panel {
      position: fixed;
      bottom: 92px;
      right: 24px;
      width: 380px;
      max-width: calc(100vw - 48px);
      height: 580px;
      max-height: calc(100vh - 120px);
      background: #ffffff;
      border-radius: 16px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.18);
      display: none;
      flex-direction: column;
      overflow: hidden;
      z-index: 999999;
      border: 1px solid #e2e8f0;
    }
    .widget-panel.open { display: flex; }
    .header {
      background: #2563EB;
      color: white;
      padding: 14px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .header h3 { margin: 0; font-size: 14px; font-weight: 600; }
    .header button { background: none; border: none; color: white; cursor: pointer; font-size: 18px; }
    .messages-container {
      flex: 1;
      padding: 16px;
      overflow-y: auto;
      background: #f8fafc;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .msg { max-width: 85%; padding: 10px 14px; border-radius: 12px; font-size: 13px; line-height: 1.45; }
    .msg-user { align-self: flex-end; background: #2563EB; color: white; }
    .msg-bot { align-self: flex-start; background: #ffffff; border: 1px solid #e2e8f0; color: #1e293b; }
    .msg-bot.refusal { background: #fffbeb; border-color: #fde68a; color: #92400e; }
    .cite-chip {
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      background: #dbeafe;
      color: #1d4ed8;
      padding: 1px 5px;
      border-radius: 4px;
      margin: 0 2px;
      cursor: pointer;
    }
    .footer {
      padding: 12px;
      background: #ffffff;
      border-top: 1px solid #e2e8f0;
      display: flex;
      gap: 8px;
    }
    .input-box {
      flex: 1;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 13px;
      outline: none;
    }
    .input-box:focus { border-color: #2563EB; }
    .send-btn {
      background: #2563EB;
      color: white;
      border: none;
      border-radius: 8px;
      padding: 0 14px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
    }
  `;
  shadow.appendChild(style);

  // Panel HTML
  const wrapper = document.createElement('div');
  wrapper.innerHTML = `
    <button class="btn-launcher" title="Chat with docs">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"></path>
        <path d="M6 6h10"></path>
        <path d="M6 10h10"></path>
      </svg>
    </button>
    <div class="widget-panel">
      <div class="header">
        <h3 id="cb-client-name">CiteBot Assistant</h3>
        <button id="cb-close-btn">&times;</button>
      </div>
      <div class="messages-container" id="cb-msgs">
        <div class="msg msg-bot">Hello! Ask any question about our verified documentation. Every answer is 100% cited.</div>
      </div>
      <form class="footer" id="cb-form">
        <input type="text" class="input-box" id="cb-input" placeholder="Ask a question..." />
        <button type="submit" class="send-btn">Send</button>
      </form>
    </div>
  `;
  shadow.appendChild(wrapper);

  // Widget Logic
  const launcher = shadow.querySelector('.btn-launcher');
  const panel = shadow.querySelector('.widget-panel');
  const closeBtn = shadow.querySelector('#cb-close-btn');
  const form = shadow.querySelector('#cb-form');
  const input = shadow.querySelector('#cb-input');
  const msgsContainer = shadow.querySelector('#cb-msgs');
  const clientNameEl = shadow.querySelector('#cb-client-name');

  let convId = null;

  // Fetch config
  fetch(`${apiUrl}/api/v1/config?deployment_id=${deploymentId}`)
    .then((r) => r.json())
    .then((cfg) => {
      if (cfg.client_name) clientNameEl.textContent = cfg.client_name;
      if (cfg.accent_color) {
        launcher.style.background = cfg.accent_color;
        shadow.querySelector('.header').style.background = cfg.accent_color;
      }
    })
    .catch(() => {});

  launcher.addEventListener('click', () => {
    panel.classList.toggle('open');
    if (panel.classList.contains('open')) input.focus();
  });

  closeBtn.addEventListener('click', () => {
    panel.classList.remove('open');
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    // Add user msg
    const userDiv = document.createElement('div');
    userDiv.className = 'msg msg-user';
    userDiv.textContent = query;
    msgsContainer.appendChild(userDiv);
    input.value = '';
    msgsContainer.scrollTop = msgsContainer.scrollHeight;

    // Loading msg
    const botDiv = document.createElement('div');
    botDiv.className = 'msg msg-bot';
    botDiv.textContent = 'Verifying evidence...';
    msgsContainer.appendChild(botDiv);
    msgsContainer.scrollTop = msgsContainer.scrollHeight;

    try {
      const res = await fetch(`${apiUrl}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query,
          conversation_id: convId,
          deployment_id: deploymentId
        })
      });
      const data = await res.json();
      convId = data.conversation_id;

      if (data.is_refusal) {
        botDiv.className = 'msg msg-bot refusal';
        botDiv.textContent = data.content;
      } else {
        // Format with citations
        let formatted = data.content.replace(/\[(\d+)\]/g, (match, num) => {
          const c = data.citations?.find((item) => item.citation_number === parseInt(num));
          const tooltip = c ? `${c.document_name} § ${c.section_heading || 'P.' + c.page_number}` : '';
          return `<span class="cite-chip" title="${tooltip}">[${num}]</span>`;
        });
        botDiv.innerHTML = formatted;
      }
    } catch (err) {
      botDiv.textContent = 'Could not retrieve verified response. Please try again.';
    }
    msgsContainer.scrollTop = msgsContainer.scrollHeight;
  });
})();
