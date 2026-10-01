import{E as e,L as t,R as n,T as r,b as i,c as a,f as o,h as s,l as c,m as l,n as u,p as d,t as f}from"./chunks/register-dashboard-card-DZx1xIi-.js";import"./unraid-server-card.js";import"./unraid-storage-card.js";import"./unraid-docker-card.js";import"./unraid-ups-card.js";import"./unraid-vm-card.js";var p=class extends a{static editorTag=e;static properties={...a.properties,_activeTab:{state:!0}};constructor(){super(),this._activeTab=`overview`}render(){let e=this.getActiveDevice(),r=this.config.title||e?.name_by_user||e?.name||`Unraid Server`;return n`
      <ha-card style="gap: 12px;">
        <div class="header">
          <div class="header-main">
            <div class="header-icon">${c(i,22)}</div>
            <div class="header-titles">
              <span class="header-title">${r} Dashboard</span>
              <span class="header-subtitle">Unified Unraid Control Center</span>
            </div>
          </div>
        </div>

        <!-- Tab Strip -->
        <div class="tab-strip">
          <button
            class="tab-btn ${this._activeTab===`overview`?`active`:``}"
            @click=${()=>this._activeTab=`overview`}
          >
            ${c(i,14)} Overview
          </button>
          <button
            class="tab-btn ${this._activeTab===`storage`?`active`:``}"
            @click=${()=>this._activeTab=`storage`}
          >
            ${c(l,14)} Storage & Disks
          </button>
          <button
            class="tab-btn ${this._activeTab===`docker`?`active`:``}"
            @click=${()=>this._activeTab=`docker`}
          >
            ${c(o,14)} Docker
          </button>
          <button
            class="tab-btn ${this._activeTab===`ups`?`active`:``}"
            @click=${()=>this._activeTab=`ups`}
          >
            ${c(d,14)} UPS Power
          </button>
          <button
            class="tab-btn ${this._activeTab===`vms`?`active`:``}"
            @click=${()=>this._activeTab=`vms`}
          >
            ${c(s,14)} VMs
          </button>
        </div>

        <!-- Tab Contents -->
        <div>
          ${this._activeTab===`overview`?n`<unraid-server-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-server-card`,embedded:!0}}></unraid-server-card>`:t}
          ${this._activeTab===`storage`?n`<unraid-storage-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-storage-card`,embedded:!0}}></unraid-storage-card>`:t}
          ${this._activeTab===`docker`?n`<unraid-docker-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-docker-card`,embedded:!0}}></unraid-docker-card>`:t}
          ${this._activeTab===`ups`?n`<unraid-ups-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-ups-card`,embedded:!0}}></unraid-ups-card>`:t}
          ${this._activeTab===`vms`?n`<unraid-vm-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-vm-card`,embedded:!0}}></unraid-vm-card>`:t}
        </div>
      </ha-card>
    `}};f({tag:r,editorTag:e,card:p,editor:u,name:`Unraid Unified Dashboard Card`,description:`All-in-one Unraid master card with tabbed overview, storage, docker, UPS, and VM monitoring.`});
