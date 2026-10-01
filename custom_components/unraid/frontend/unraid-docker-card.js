import{C as e,D as t,L as n,O as r,R as i,c as a,f as o,l as s,r as c,t as l,u,v as d,w as f,y as p}from"./chunks/register-dashboard-card-Ck7vsCPn.js";function m(e){let t=e.split(`.`)[1]||``;return t.replace(/^.*?_container_restart_/,``).replace(/^.*?_docker_container_restart_/,``).replace(/^.*?_container_autostart_/,``).replace(/^.*?_docker_container_autostart_/,``).replace(/^.*?_container_update_/,``).replace(/^.*?_docker_container_update_/,``).replace(/^.*?_docker_container_/,``).replace(/^.*?_container_switch_/,``).replace(/^docker_container_/,``).replace(/^container_switch_/,``).replace(/_cpu$/,``).replace(/_memory_usage$/,``).replace(/_memory$/,``).replace(/_docker_container$/,``).replace(/_container_switch$/,``).replace(/^.*?_container_/,``)||t}var h=class extends a{static editorTag=r;static properties={...a.properties,_filter:{state:!0},_viewMode:{state:!0}};constructor(){super(),this._filter=`all`,this._viewMode=`grid`}willUpdate(e){super.willUpdate(e),e.has(`config`)&&this.config.view_mode&&e.get(`config`)?.view_mode!==this.config.view_mode&&(this._viewMode=this.config.view_mode)}handleToggle(e,t,n){(!t||confirm(`Are you sure you want to stop container "${n}"?`))&&this.toggleEntity(e)}getContainers(){let e=this.getEntities(`docker_container_autostart`,`switch`),t=new Set(e.map(e=>e.entity_id)),n=this.getEntities(`docker_container`,`switch`).filter(e=>!t.has(e.entity_id)),r=this.getEntities(`docker_container_restart`,`button`),i=this.getEntities(`container_cpu`),a=this.getEntities(`container_memory_usage`),o=this.getEntities(`docker_container_update`,`update`),s=[];for(let t of n){let n=m(t.entity_id),c=t.attributes.friendly_name||n,l=t.state===`on`,u=r.find(e=>m(e.entity_id)===n),d=e.find(e=>m(e.entity_id)===n),f=i.find(e=>m(e.entity_id)===n),p=a.find(e=>m(e.entity_id)===n),h=o.find(e=>m(e.entity_id)===n);s.push({id:n,name:c,isRunning:l,switchEntityId:t.entity_id,restartEntityId:u?.entity_id,autostartEntityId:d?.entity_id,cpuPct:f?.state?parseFloat(f.state):void 0,memoryUsage:p?.state&&p.state!==`unavailable`?`${p.state} ${p.attributes.unit_of_measurement||`B`}`:void 0,hasUpdate:h?.state===`on`,updateEntityId:h?.entity_id})}return s.sort((e,t)=>e.isRunning&&!t.isRunning?-1:!e.isRunning&&t.isRunning?1:e.name.localeCompare(t.name))}render(){let t=this.getContainers(),r=t.filter(e=>e.isRunning).length,a=t.length-r,c=t.filter(e=>e.hasUpdate).length,l=this.getEntity(`check_container_updates`,`button`),m=t.filter(e=>this._filter===`running`?e.isRunning:this._filter===`stopped`?!e.isRunning:this._filter!==`updates`||e.hasUpdate),h=i`
      <span class="badge ${r>0?`badge-online`:`badge-standby`}">
        ${r} Running
      </span>
      ${c>0?i`
            <span class="badge badge-warning">
              ${s(u,12)}
              <span>${c} Updates</span>
            </span>
          `:n}
    `;return i`
      <ha-card>
        ${this.renderHeader(this.config.title||`Docker Containers`,`${r} running • ${a} stopped`,o,h)}

        <!-- Top Controls & Filter Bar -->
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;">
          <div style="display: flex; gap: 4px; overflow-x: auto;">
            <button
              class="tab-btn ${this._filter===`all`?`active`:``}"
              @click=${()=>this._filter=`all`}
            >
              All (${t.length})
            </button>
            <button
              class="tab-btn ${this._filter===`running`?`active`:``}"
              @click=${()=>this._filter=`running`}
            >
              Running (${r})
            </button>
            <button
              class="tab-btn ${this._filter===`stopped`?`active`:``}"
              @click=${()=>this._filter=`stopped`}
            >
              Stopped (${a})
            </button>
            ${c>0?i`
                  <button
                    class="tab-btn ${this._filter===`updates`?`active`:``}"
                    style="color: var(--unraid-warning);"
                    @click=${()=>this._filter=`updates`}
                  >
                    Updates (${c})
                  </button>
                `:n}
          </div>

          <div style="display: flex; align-items: center; gap: 6px;">
            ${l?i`
                  <button
                    class="btn"
                    title="Check for updates"
                    @click=${()=>this.pressButton(l.entity_id)}
                  >
                    Check Updates
                  </button>
                `:n}
            <button
              class="btn-icon"
              title="Toggle View Mode"
              @click=${()=>this._viewMode=this._viewMode===`grid`?`list`:`grid`}
            >
              ${s(this._viewMode===`grid`?f:e,18)}
            </button>
          </div>
        </div>

        <!-- Containers Display (Grid or List View) -->
        ${this._viewMode===`grid`?i`
              <div class="container-grid">
                ${m.map(e=>i`
                    <div
                      class="container-tile"
                      @click=${()=>this.openMoreInfo(e.switchEntityId)}
                    >
                      <div style="display: flex; align-items: center; gap: 8px; min-width: 0;">
                        <span class="status-dot ${e.isRunning?`online`:`offline`}"></span>
                        <span class="tile-name" title="${e.name}">${e.name}</span>
                      </div>
                      <div style="display: flex; align-items: center; gap: 4px;">
                        ${e.hasUpdate?i`<span style="color: var(--unraid-warning);">${s(u,14)}</span>`:n}
                        ${e.restartEntityId?i`
                              <button
                                class="btn-icon"
                                style="padding: 2px;"
                                title="Restart ${e.name}"
                                @click=${t=>{t.stopPropagation(),this.pressButton(e.restartEntityId)}}
                              >
                                ${s(p,14)}
                              </button>
                            `:n}
                        <button
                          class="btn-icon"
                          style="padding: 2px; color: ${e.isRunning?`var(--unraid-online)`:`var(--unraid-subtext)`};"
                          title="${e.isRunning?`Stop`:`Start`} ${e.name}"
                          @click=${t=>{t.stopPropagation(),this.handleToggle(e.switchEntityId,e.isRunning,e.name)}}
                        >
                          ${s(d,14)}
                        </button>
                      </div>
                    </div>
                  `)}
              </div>
            `:i`
              <div class="item-list">
                ${m.map(e=>i`
                    <div class="list-row">
                      <div class="row-left">
                        <span class="status-dot ${e.isRunning?`online`:`offline`}"></span>
                        <span style="font-weight: 600; min-width: 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                          ${e.name}
                        </span>
                        ${e.cpuPct===void 0?n:i`<span style="font-size: 0.72rem; color: var(--unraid-subtext);">${e.cpuPct}% CPU</span>`}
                        ${e.memoryUsage?i`<span style="font-size: 0.72rem; color: var(--unraid-subtext);">${e.memoryUsage}</span>`:n}
                      </div>
                      <div class="row-right">
                        ${e.hasUpdate?i`
                              <span class="badge badge-warning">Update Available</span>
                            `:n}
                        ${e.restartEntityId?i`
                              <button
                                class="btn"
                                style="padding: 3px 8px;"
                                @click=${()=>this.pressButton(e.restartEntityId)}
                              >
                                ${s(p,13)}
                                <span>Restart</span>
                              </button>
                            `:n}
                        <button
                          class="btn ${e.isRunning?`btn`:`btn-primary`}"
                          style="padding: 3px 8px;"
                          @click=${()=>this.handleToggle(e.switchEntityId,e.isRunning,e.name)}
                        >
                          ${s(d,13)}
                          <span>${e.isRunning?`Stop`:`Start`}</span>
                        </button>
                      </div>
                    </div>
                  `)}
              </div>
            `}
      </ha-card>
    `}};l({tag:t,editorTag:r,card:h,editor:c,name:`Unraid Docker Containers Card`,description:`Monitor, start, stop, restart, and update Docker containers in grid or list view.`});
