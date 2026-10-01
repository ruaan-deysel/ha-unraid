import{L as e,M as t,R as n,S as r,_ as i,a,c as o,d as s,g as c,j as l,l as u,m as d,t as f,u as p,x as m}from"./chunks/register-dashboard-card-Ck7vsCPn.js";function h(e,t){let n=t.replace(/[.*+?^${}()|[\]\\]/g,`\\$&`);return RegExp(`(?:^|[._])${n}(?:[._]|$)`).test(e)}f({tag:l,editorTag:t,card:class extends o{static editorTag=t;getDisks(){let e=this.getEntities(`disk_usage`),t=this.getEntities(`disk_temperature`),n=this.getEntities(`disk_error_count`),r=this.getEntities(`disk_spin`,`switch`),i=new Map;for(let t of e){let e=(t.entity_id.split(`.`)[1]||``).replace(/_disk_usage|_usage$/,``),n=t.attributes.friendly_name||e,r=n.toLowerCase().includes(`parity`),a=n.toLowerCase().includes(`cache`)||n.toLowerCase().includes(`pool`),o=n.toLowerCase().includes(`boot`)||n.toLowerCase().includes(`flash`),s=e;i.set(s,{id:s,name:n,isParity:r,isCache:a,isBoot:o,usagePct:Math.round(Number(t.state)||0),temp:`*`,errors:0,isSpinning:!1,freeSpace:t.attributes.free,totalSpace:t.attributes.total})}for(let e of t)for(let[t,n]of i.entries())if(h(e.entity_id,t)){n.temp=e.state!==`unavailable`&&e.state!==`unknown`?`${e.state}°C`:`*`;break}for(let e of n)for(let[t,n]of i.entries())if(h(e.entity_id,t)){n.errors=Number(e.state)||0;break}for(let e of r)for(let[t,n]of i.entries())if(h(e.entity_id,t)){n.isSpinning=e.state===`on`,n.spinEntityId=e.entity_id;break}return Array.from(i.values()).sort((e,t)=>e.isParity===t.isParity?e.isCache===t.isCache?e.name.localeCompare(t.name,void 0,{numeric:!0}):e.isCache?1:-1:e.isParity?-1:1)}render(){let t=this.getEntity(`array_usage`),a=this.getEntity(`parity_status`),o=this.getEntity(`parity_progress`),l=this.getEntity(`parity_check`,`switch`),f=this.getEntity(`last_parity_check_date`),h=this.getEntity(`last_parity_check_errors`),g=Math.round(Number(t?.state)||0),_=t?.attributes?.capacity_used||``,v=t?.attributes?.capacity_total||``,y=t?.attributes?.capacity_free||``,b=o&&!isNaN(Number(o.state))&&Number(o.state)>0,x=Math.round(Number(o?.state)||0),S=a?.state?.toLowerCase()===`on`||a?.state?.toLowerCase()===`ok`||a?.state===`Valid`,C=this.getDisks(),w=n`
      <span class="badge ${S?`badge-online`:`badge-warning`}">
        ${u(S?r:m,13)}
        <span>${S?`Parity Valid`:`Parity Check Needed`}</span>
      </span>
    `;return n`
      <ha-card>
        ${this.renderHeader(this.config.title||`Storage Array & Disks`,`${_||`${g}%`} used of ${v||`Array`}${y?` (${y} Free)`:``}`,d,w)}

        <!-- Array Capacity Bar -->
        <div style="display: flex; flex-direction: column; gap: 4px;">
          <div style="display: flex; justify-content: space-between; font-size: 0.76rem; font-weight: 600;">
            <span>Array Capacity</span>
            <span>${g}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: ${g}%;"></div>
          </div>
        </div>

        <!-- Parity Check Status & Action Banner -->
        <div class="list-row" style="background: color-mix(in srgb, var(--unraid-text) 5%, transparent);">
          <div class="row-left">
            <div style="color: ${S?`var(--unraid-online)`:`var(--unraid-warning)`}">
              ${u(S?s:p,18)}
            </div>
            <div style="display: flex; flex-direction: column; min-width: 0;">
              <span style="font-weight: 600; font-size: 0.78rem;">
                ${b?`Parity Check In Progress (${x}%)`:`Parity Status: ${S?`Valid`:`Check Needed`}`}
              </span>
              <span style="font-size: 0.7rem; color: var(--unraid-subtext);">
                ${f?.state?`Last check: ${f.state}`:`Parity healthy`}
                ${h?.state&&h.state!==`0`?` • ${h.state} errors`:``}
              </span>
            </div>
          </div>
          <div class="row-right">
            ${l?n`
                  <button
                    class="btn ${b?`btn`:`btn-primary`}"
                    @click=${()=>this.toggleEntity(l.entity_id)}
                  >
                    ${u(b?c:i,14)}
                    <span>${b?`Cancel`:`Check Now`}</span>
                  </button>
                `:e}
          </div>
        </div>

        <!-- Disk Trays List -->
        <div class="item-list">
          ${C.length>0?C.map(e=>{let t=parseFloat(e.temp),r=isNaN(t)?`var(--unraid-standby)`:t>45?`var(--unraid-error)`:t>36?`var(--unraid-warning)`:`var(--unraid-online)`;return n`
                  <div class="list-row">
                    <div class="row-left">
                      <!-- Spin status button -->
                      ${e.spinEntityId?n`
                            <button
                              class="badge ${e.isSpinning?`badge-online`:`badge-standby`}"
                              style="cursor: pointer; border: none;"
                              title="Click to spin ${e.isSpinning?`down`:`up`}"
                              @click=${()=>this.toggleEntity(e.spinEntityId)}
                            >
                              <span class="status-dot ${e.isSpinning?`online`:`offline`}"></span>
                              <span>${e.isSpinning?`Active`:`Standby`}</span>
                            </button>
                          `:n`
                            <span class="badge ${e.isSpinning?`badge-online`:`badge-standby`}">
                              <span>${e.isSpinning?`Active`:`Standby`}</span>
                            </span>
                          `}

                      <span style="font-weight: 600; min-width: 80px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${e.name}
                      </span>
                    </div>

                    <div class="row-right">
                      <!-- Temperature Chip -->
                      <span class="badge" style="color: ${r}; background: color-mix(in srgb, ${r} 12%, transparent);">
                        ${e.temp}
                      </span>

                      <!-- Error Counter -->
                      ${e.errors>0?n`
                            <span class="badge badge-error">
                              ${e.errors} err
                            </span>
                          `:n`
                            <span class="badge badge-online" style="font-size: 0.68rem;">0 err</span>
                          `}

                      <!-- Utilization -->
                      <div style="display: flex; align-items: center; gap: 6px; width: 85px;">
                        <div class="progress-bar" style="height: 4px;">
                          <div
                            class="progress-fill"
                            style="width: ${e.usagePct}%; background: ${e.isCache?`var(--unraid-info)`:`var(--unraid-accent)`};"
                          ></div>
                        </div>
                        <span style="font-size: 0.7rem; font-family: monospace; color: var(--unraid-subtext);">
                          ${e.usagePct}%
                        </span>
                      </div>
                    </div>
                  </div>
                `}):n`<div style="text-align: center; color: var(--unraid-subtext); font-size: 0.8rem; padding: 12px;">No disk devices found</div>`}
        </div>
      </ha-card>
    `}},editor:a,name:`Unraid Storage & Disks Card`,description:`Array capacity, parity checks, and interactive disk tray with spin state controls.`});
