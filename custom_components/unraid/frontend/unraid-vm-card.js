import{F as e,I as t,L as n,R as r,c as i,h as a,l as o,s,t as c,v as l,y as u}from"./chunks/register-dashboard-card-DZx1xIi-.js";function d(e){let t=e.split(`.`)[1]||``;return t.replace(/^.*?_vm_reboot_/,``).replace(/^vm_reboot_/,``).replace(/^.*?_virtual_machine_status_/,``).replace(/^virtual_machine_status_/,``).replace(/^.*?_virtual_machine_/,``).replace(/^virtual_machine_/,``).replace(/_status$/,``).replace(/_virtual_machine$/,``)||t}c({tag:e,editorTag:t,card:class extends i{static editorTag=t;handleToggle(e,t,n){(!t||confirm(`Are you sure you want to shut down virtual machine "${n}"?`))&&this.toggleEntity(e)}getVms(){let e=this.getEntities(`virtual_machine`,`switch`),t=this.getEntities(`virtual_machine_status`,`sensor`),n=this.getEntities(`vm_reboot`,`button`),r=[];for(let i of e){let e=d(i.entity_id),a=i.attributes.friendly_name||e,o=i.state===`on`,s=t.find(t=>d(t.entity_id)===e)?.state||(o?`running`:`shut off`),c=n.find(t=>d(t.entity_id)===e);r.push({id:e,name:a,isRunning:o,status:s,switchEntityId:i.entity_id,rebootEntityId:c?.entity_id})}return r.sort((e,t)=>e.isRunning&&!t.isRunning?-1:!e.isRunning&&t.isRunning?1:e.name.localeCompare(t.name))}render(){let e=this.getVms(),t=e.filter(e=>e.isRunning).length,i=r`
      <span class="badge ${t>0?`badge-online`:`badge-standby`}">
        ${t} Running
      </span>
    `;return r`
      <ha-card>
        ${this.renderHeader(this.config.title||`Virtual Machines`,`${t} running of ${e.length} VMs`,a,i)}

        <div class="item-list">
          ${e.length>0?e.map(e=>r`
                  <div class="list-row">
                    <div class="row-left">
                      <span class="status-dot ${e.isRunning?`online`:`offline`}"></span>
                      <div style="display: flex; flex-direction: column;">
                        <span style="font-weight: 600;">${e.name}</span>
                        <span style="font-size: 0.7rem; color: var(--unraid-subtext); text-transform: capitalize;">
                          ${e.status}
                        </span>
                      </div>
                    </div>
                    <div class="row-right">
                      ${e.rebootEntityId?r`
                            <button
                              class="btn"
                              style="padding: 3px 8px;"
                              title="Reboot VM"
                              @click=${()=>this.pressButton(e.rebootEntityId)}
                            >
                              ${o(u,13)}
                              <span>Reboot</span>
                            </button>
                          `:n}
                      <button
                        class="btn ${e.isRunning?`btn`:`btn-primary`}"
                        style="padding: 3px 8px;"
                        @click=${()=>this.handleToggle(e.switchEntityId,e.isRunning,e.name)}
                      >
                        ${o(l,13)}
                        <span>${e.isRunning?`Stop`:`Start`}</span>
                      </button>
                    </div>
                  </div>
                `):r`<div style="text-align: center; color: var(--unraid-subtext); font-size: 0.8rem; padding: 12px;">No virtual machines configured</div>`}
        </div>
      </ha-card>
    `}},editor:s,name:`Unraid Virtual Machines Card`,description:`Monitor and manage Unraid virtual machines.`});
