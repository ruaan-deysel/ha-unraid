import{A as e,L as t,R as n,b as r,c as i,i as a,k as o,l as s,t as c,u as l}from"./chunks/register-dashboard-card-DZx1xIi-.js";c({tag:o,editorTag:e,card:class extends i{static editorTag=e;formatUptime(e){if(!e)return`Unknown`;let t=e.trim();if(/^\d+(\.\d+)?$/.test(t)){let e=Number(t),n=Math.floor(e/86400),r=Math.floor(e%86400/3600);return n>0?`${n}d ${r}h`:`${r}h`}let n=new Date(e);if(!isNaN(n.getTime())){let e=Date.now()-n.getTime(),t=Math.floor(e/864e5),r=Math.floor(e/36e5%24);return t>0?`${t}d ${r}h`:`${r}h`}return e}render(){let e=this.getActiveDevice(),i=this.config.title||e?.name_by_user||e?.name||`Unraid Server`,a=this.getEntity(`cpu_usage`),o=this.getEntity(`ram_usage`),c=this.getEntity(`array_usage`),u=this.getEntity(`array_state`),d=this.getEntity(`system_temperature`)||this.getEntity(`temperature_average`),f=this.getEntity(`cpu_power`),p=this.getEntity(`uptime`),m=this.getEntity(`notifications_unread_alert`),h=this.getEntity(`network_interface_ip`),g=Math.round(Number(a?.state)||0),_=Math.round(Number(o?.state)||0),v=Math.round(Number(c?.state)||0),y=u?.state?.toLowerCase()===`started`||u?.state===`Normal`,b=Number(m?.state)||0,x=a?.attributes?.cpu_model||(e?.model??`Multi-Core CPU`),S=o?.attributes?.used||``,C=o?.attributes?.total||``,w=c?.attributes?.capacity_used||``,T=c?.attributes?.capacity_total||``,E=n`
      <span class="badge ${y?`badge-online`:`badge-error`}">
        <span class="pulse-dot"></span>
        <span>Array ${u?.state||(y?`Started`:`Stopped`)}</span>
      </span>
      ${b>0?n`
            <span class="badge badge-error">
              ${s(l,13)}
              <span>${b}</span>
            </span>
          `:t}
    `;return n`
      <ha-card>
        ${this.renderHeader(i,`${e?.model||`Unraid OS`} • Up ${this.formatUptime(p?.state)}`,r,E)}

        <!-- Conic Ring Gauges -->
        <div class="rings-grid">
          <!-- CPU -->
          <div class="ring-card">
            <div
              class="ring-gauge"
              style="--pct: ${g}; --ring-color: ${g>80?`var(--unraid-error)`:g>50?`var(--unraid-warning)`:`var(--unraid-online)`}"
            >
              <span class="ring-content">${g}%</span>
            </div>
            <span class="ring-label">CPU Load</span>
            <span class="ring-subtext">
              ${d?.state?`${d.state}°C`:``}${f?.state?` • ${f.state}W`:``}
            </span>
          </div>

          <!-- RAM -->
          <div class="ring-card">
            <div
              class="ring-gauge"
              style="--pct: ${_}; --ring-color: ${_>85?`var(--unraid-error)`:`var(--unraid-info)`}"
            >
              <span class="ring-content">${_}%</span>
            </div>
            <span class="ring-label">Memory</span>
            <span class="ring-subtext">${S&&C?`${S} / ${C}`:`${_}% used`}</span>
          </div>

          <!-- Array -->
          <div class="ring-card">
            <div
              class="ring-gauge"
              style="--pct: ${v}; --ring-color: var(--unraid-accent)"
            >
              <span class="ring-content">${v}%</span>
            </div>
            <span class="ring-label">Array Storage</span>
            <span class="ring-subtext">${w&&T?`${w} / ${T}`:`${v}% used`}</span>
          </div>
        </div>

        ${this.config.show_system_info===!1?t:n`
              <div class="divider"></div>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="detail-label">Processor</span>
                  <span class="detail-val" title="${x}">${x}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">LAN IP Address</span>
                  <span class="detail-val">${h?.state||`Connected`}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">System Health</span>
                  <span class="detail-val" style="color: ${b===0?`var(--unraid-online)`:`var(--unraid-error)`}">
                    ${b===0?`Normal • Healthy`:`${b} Active Alerts`}
                  </span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">OS Version</span>
                  <span class="detail-val">${e?.sw_version||`Unraid OS`}</span>
                </div>
              </div>
            `}
      </ha-card>
    `}},editor:a,name:`Unraid Server Overview Card`,description:`Server metrics, CPU/RAM ring gauges, and hardware health.`});
