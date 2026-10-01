import{L as e,N as t,P as n,R as r,c as i,o as a,p as o,t as s}from"./chunks/register-dashboard-card-Ck7vsCPn.js";s({tag:t,editorTag:n,card:class extends i{static editorTag=n;render(){let t=this.getEntity(`ups_status`),n=this.getEntity(`ups_battery`),i=this.getEntity(`ups_load`),a=this.getEntity(`ups_runtime`),s=this.getEntity(`ups_power`),c=this.getEntity(`ups_output_voltage`),l=this.getEntity(`ups_battery_health`),u=!!(t&&t.state!==`unavailable`&&t.state!==`unknown`),d=u&&t?t.state:t?.state||`Unavailable`,f=u&&d.toLowerCase().includes(`online`),p=u&&(d.toLowerCase().includes(`battery`)||d.toLowerCase().includes(`discharge`)),m=!u||d===`Unavailable`||d===`unavailable`,h=n&&n.state!==`unavailable`&&n.state!==`unknown`&&n?Math.round(Number(n.state)||0):null,g=i&&i.state!==`unavailable`&&i.state!==`unknown`&&i?Math.round(Number(i.state)||0):null,_=s&&s.state!==`unavailable`&&s.state!==`unknown`&&s?`${s.state} W`:null,v=a&&a.state!==`unavailable`&&a.state!==`unknown`&&a?`${a.state} min`:null,y=c&&c.state!==`unavailable`&&c.state!==`unknown`&&c?`${c.state} V`:null,b=l&&l.state!==`unavailable`&&l.state!==`unknown`&&l?l.state:null,x=r`
      <span class="badge ${m?`badge-standby`:f?`badge-online`:p?`badge-warning`:`badge-error`}">
        ${m?e:r`<span class="pulse-dot"></span>`}
        <span>${m?`Unavailable`:d}</span>
      </span>
    `;return r`
      <ha-card>
        ${this.renderHeader(this.config.title||`UPS Power & Battery`,t?.attributes?.model||`Uninterruptible Power Supply`,o,x)}

        <!-- Ring Gauges -->
        <div class="rings-grid" style="grid-template-columns: repeat(2, 1fr);">
          <!-- Battery -->
          <div class="ring-card">
            <div
              class="ring-gauge"
              style="--pct: ${h??0}; --ring-color: ${h===null?`var(--unraid-border)`:h<20?`var(--unraid-error)`:h<50?`var(--unraid-warning)`:`var(--unraid-online)`}"
            >
              <span class="ring-content">${h===null?`—`:`${h}%`}</span>
            </div>
            <span class="ring-label">Battery Level</span>
            <span class="ring-subtext">${v?`${v} left`:h===null?`No Data`:`Healthy`}</span>
          </div>

          <!-- Load -->
          <div class="ring-card">
            <div
              class="ring-gauge"
              style="--pct: ${g??0}; --ring-color: ${g===null?`var(--unraid-border)`:g>80?`var(--unraid-error)`:g>50?`var(--unraid-warning)`:`var(--unraid-info)`}"
            >
              <span class="ring-content">${g===null?`—`:`${g}%`}</span>
            </div>
            <span class="ring-label">UPS Load</span>
            <span class="ring-subtext">${_||(g===null?`No Data`:`${g}% capacity`)}</span>
          </div>
        </div>

        <div class="divider"></div>

        <!-- Power & Electrical Specs -->
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">Runtime Remaining</span>
            <span class="detail-val">${v||`—`}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Power Consumption</span>
            <span class="detail-val">${_||`—`}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Output Voltage</span>
            <span class="detail-val">${y||`—`}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Battery Health</span>
            <span class="detail-val" style="${b?`color: var(--unraid-online);`:``}">${b||`—`}</span>
          </div>
        </div>
      </ha-card>
    `}},editor:a,name:`Unraid Power & UPS Card`,description:`Monitor UPS battery level, power draw in Watts, load %, and estimated runtime.`});
