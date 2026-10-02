var e=globalThis,t=e.ShadowRoot&&(e.ShadyCSS===void 0||e.ShadyCSS.nativeShadow)&&`adoptedStyleSheets`in Document.prototype&&`replace`in CSSStyleSheet.prototype,n=Symbol(),r=new WeakMap,i=class{constructor(e,t,r){if(this._$cssResult$=!0,r!==n)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o,n=this.t;if(t&&e===void 0){let t=n!==void 0&&n.length===1;t&&(e=r.get(n)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),t&&r.set(n,e))}return e}toString(){return this.cssText}},a=e=>new i(typeof e==`string`?e:e+``,void 0,n),o=(e,...t)=>new i(e.length===1?e[0]:t.reduce((t,n,r)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if(typeof e==`number`)return e;throw Error(`Value passed to 'css' function must be a 'css' function result: `+e+`. Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.`)})(n)+e[r+1],e[0]),e,n),s=(n,r)=>{if(t)n.adoptedStyleSheets=r.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let t of r){let r=document.createElement(`style`),i=e.litNonce;i!==void 0&&r.setAttribute(`nonce`,i),r.textContent=t.cssText,n.appendChild(r)}},c=t?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t=``;for(let n of e.cssRules)t+=n.cssText;return a(t)})(e):e,{is:l,defineProperty:u,getOwnPropertyDescriptor:d,getOwnPropertyNames:f,getOwnPropertySymbols:p,getPrototypeOf:m}=Object,h=globalThis,g=h.trustedTypes,_=g?g.emptyScript:``,v=h.reactiveElementPolyfillSupport,y=(e,t)=>e,b={toAttribute(e,t){switch(t){case Boolean:e=e?_:null;break;case Object:case Array:e=e==null?e:JSON.stringify(e)}return e},fromAttribute(e,t){let n=e;switch(t){case Boolean:n=e!==null;break;case Number:n=e===null?null:Number(e);break;case Object:case Array:try{n=JSON.parse(e)}catch{n=null}}return n}},x=(e,t)=>!l(e,t),S={attribute:!0,type:String,converter:b,reflect:!1,useDefault:!1,hasChanged:x};Symbol.metadata??=Symbol(`metadata`),h.litPropertyMetadata??=new WeakMap;var C=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=S){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){let n=Symbol(),r=this.getPropertyDescriptor(e,n,t);r!==void 0&&u(this.prototype,e,r)}}static getPropertyDescriptor(e,t,n){let{get:r,set:i}=d(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:r,set(t){let a=r?.call(this);i?.call(this,t),this.requestUpdate(e,a,n)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??S}static _$Ei(){if(this.hasOwnProperty(y(`elementProperties`)))return;let e=m(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(y(`finalized`)))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(y(`properties`))){let e=this.properties,t=[...f(e),...p(e)];for(let n of t)this.createProperty(n,e[n])}let e=this[Symbol.metadata];if(e!==null){let t=litPropertyMetadata.get(e);if(t!==void 0)for(let[e,n]of t)this.elementProperties.set(e,n)}this._$Eh=new Map;for(let[e,t]of this.elementProperties){let n=this._$Eu(e,t);n!==void 0&&this._$Eh.set(n,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){let t=[];if(Array.isArray(e)){let n=new Set(e.flat(1/0).reverse());for(let e of n)t.unshift(c(e))}else e!==void 0&&t.push(c(e));return t}static _$Eu(e,t){let n=t.attribute;return!1===n?void 0:typeof n==`string`?n:typeof e==`string`?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){let e=new Map,t=this.constructor.elementProperties;for(let n of t.keys())this.hasOwnProperty(n)&&(e.set(n,this[n]),delete this[n]);e.size>0&&(this._$Ep=e)}createRenderRoot(){let e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return s(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,n){this._$AK(e,n)}_$ET(e,t){let n=this.constructor.elementProperties.get(e),r=this.constructor._$Eu(e,n);if(r!==void 0&&!0===n.reflect){let i=(n.converter?.toAttribute===void 0?b:n.converter).toAttribute(t,n.type);this._$Em=e,i==null?this.removeAttribute(r):this.setAttribute(r,i),this._$Em=null}}_$AK(e,t){let n=this.constructor,r=n._$Eh.get(e);if(r!==void 0&&this._$Em!==r){let e=n.getPropertyOptions(r),i=typeof e.converter==`function`?{fromAttribute:e.converter}:e.converter?.fromAttribute===void 0?b:e.converter;this._$Em=r;let a=i.fromAttribute(t,e.type);this[r]=a??this._$Ej?.get(r)??a,this._$Em=null}}requestUpdate(e,t,n,r=!1,i){if(e!==void 0){let a=this.constructor;if(!1===r&&(i=this[e]),n??=a.getPropertyOptions(e),!((n.hasChanged??x)(i,t)||n.useDefault&&n.reflect&&i===this._$Ej?.get(e)&&!this.hasAttribute(a._$Eu(e,n))))return;this.C(e,t,n)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:n,reflect:r,wrapped:i},a){n&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,a??t??this[e]),!0!==i||a!==void 0)||(this._$AL.has(e)||(this.hasUpdated||n||(t=void 0),this._$AL.set(e,t)),!0===r&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}let e=this.constructor.elementProperties;if(e.size>0)for(let[t,n]of e){let{wrapped:e}=n,r=this[t];!0!==e||this._$AL.has(t)||r===void 0||this.C(t,void 0,n,r)}}let e=!1,t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};C.elementStyles=[],C.shadowRootOptions={mode:`open`},C[y(`elementProperties`)]=new Map,C[y(`finalized`)]=new Map,v?.({ReactiveElement:C}),(h.reactiveElementVersions??=[]).push(`2.1.2`);var w=globalThis,T=e=>e,E=w.trustedTypes,D=E?E.createPolicy(`lit-html`,{createHTML:e=>e}):void 0,O=`$lit$`,k=`lit$${Math.random().toFixed(9).slice(2)}$`,ee=`?`+k,A=`<${ee}>`,j=document,M=()=>j.createComment(``),N=e=>e===null||typeof e!=`object`&&typeof e!=`function`,P=Array.isArray,te=e=>P(e)||typeof e?.[Symbol.iterator]==`function`,F="[ \t\n\f\r]",I=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,ne=/-->/g,re=/>/g,L=RegExp(`>|${F}(?:([^\\s"'>=/]+)(${F}*=${F}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,`g`),ie=/'/g,ae=/"/g,oe=/^(?:script|style|textarea|title)$/i,R=(e=>(t,...n)=>({_$litType$:e,strings:t,values:n}))(1),z=Symbol.for(`lit-noChange`),B=Symbol.for(`lit-nothing`),se=new WeakMap,V=j.createTreeWalker(j,129);function ce(e,t){if(!P(e)||!e.hasOwnProperty(`raw`))throw Error(`invalid template strings array`);return D===void 0?t:D.createHTML(t)}var le=(e,t)=>{let n=e.length-1,r=[],i,a=t===2?`<svg>`:t===3?`<math>`:``,o=I;for(let t=0;t<n;t++){let n=e[t],s,c,l=-1,u=0;for(;u<n.length&&(o.lastIndex=u,c=o.exec(n),c!==null);)u=o.lastIndex,o===I?c[1]===`!--`?o=ne:c[1]===void 0?c[2]===void 0?c[3]!==void 0&&(o=L):(oe.test(c[2])&&(i=RegExp(`</`+c[2],`g`)),o=L):o=re:o===L?c[0]===`>`?(o=i??I,l=-1):c[1]===void 0?l=-2:(l=o.lastIndex-c[2].length,s=c[1],o=c[3]===void 0?L:c[3]===`"`?ae:ie):o===ae||o===ie?o=L:o===ne||o===re?o=I:(o=L,i=void 0);let d=o===L&&e[t+1].startsWith(`/>`)?` `:``;a+=o===I?n+A:l>=0?(r.push(s),n.slice(0,l)+O+n.slice(l)+k+d):n+k+(l===-2?t:d)}return[ce(e,a+(e[n]||`<?>`)+(t===2?`</svg>`:t===3?`</math>`:``)),r]},H=class e{constructor({strings:t,_$litType$:n},r){let i;this.parts=[];let a=0,o=0,s=t.length-1,c=this.parts,[l,u]=le(t,n);if(this.el=e.createElement(l,r),V.currentNode=this.el.content,n===2||n===3){let e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;(i=V.nextNode())!==null&&c.length<s;){if(i.nodeType===1){if(i.hasAttributes())for(let e of i.getAttributeNames())if(e.endsWith(O)){let t=u[o++],n=i.getAttribute(e).split(k),r=/([.?@])?(.*)/.exec(t);c.push({type:1,index:a,name:r[2],strings:n,ctor:r[1]===`.`?fe:r[1]===`?`?pe:r[1]===`@`?me:W}),i.removeAttribute(e)}else e.startsWith(k)&&(c.push({type:6,index:a}),i.removeAttribute(e));if(oe.test(i.tagName)){let e=i.textContent.split(k),t=e.length-1;if(t>0){i.textContent=E?E.emptyScript:``;for(let n=0;n<t;n++)i.append(e[n],M()),V.nextNode(),c.push({type:2,index:++a});i.append(e[t],M())}}}else if(i.nodeType===8){if(i.data===ee)c.push({type:2,index:a});else{let e=-1;for(;(e=i.data.indexOf(k,e+1))!==-1;)c.push({type:7,index:a}),e+=k.length-1}}a++}}static createElement(e,t){let n=j.createElement(`template`);return n.innerHTML=e,n}};function U(e,t,n=e,r){if(t===z)return t;let i=r===void 0?n._$Cl:n._$Co?.[r],a=N(t)?void 0:t._$litDirective$;return i?.constructor!==a&&(i?._$AO?.(!1),a===void 0?i=void 0:(i=new a(e),i._$AT(e,n,r)),r===void 0?n._$Cl=i:(n._$Co??=[])[r]=i),i!==void 0&&(t=U(e,i._$AS(e,t.values),i,r)),t}var ue=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:t},parts:n}=this._$AD,r=(e?.creationScope??j).importNode(t,!0);V.currentNode=r;let i=V.nextNode(),a=0,o=0,s=n[0];for(;s!==void 0;){if(a===s.index){let t;s.type===2?t=new de(i,i.nextSibling,this,e):s.type===1?t=new s.ctor(i,s.name,s.strings,this,e):s.type===6&&(t=new he(i,this,e)),this._$AV.push(t),s=n[++o]}a!==s?.index&&(i=V.nextNode(),a++)}return V.currentNode=j,r}p(e){let t=0;for(let n of this._$AV)n!==void 0&&(n.strings===void 0?n._$AI(e[t]):(n._$AI(e,n,t),t+=n.strings.length-2)),t++}},de=class e{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,n,r){this.type=2,this._$AH=B,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=n,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=U(this,e,t),N(e)?e===B||e==null||e===``?(this._$AH!==B&&this._$AR(),this._$AH=B):e!==this._$AH&&e!==z&&this._(e):e._$litType$===void 0?e.nodeType===void 0?te(e)?this.k(e):this._(e):this.T(e):this.$(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==B&&N(this._$AH)?this._$AA.nextSibling.data=e:this.T(j.createTextNode(e)),this._$AH=e}$(e){let{values:t,_$litType$:n}=e,r=typeof n==`number`?this._$AC(e):(n.el===void 0&&(n.el=H.createElement(ce(n.h,n.h[0]),this.options)),n);if(this._$AH?._$AD===r)this._$AH.p(t);else{let e=new ue(r,this),n=e.u(this.options);e.p(t),this.T(n),this._$AH=e}}_$AC(e){let t=se.get(e.strings);return t===void 0&&se.set(e.strings,t=new H(e)),t}k(t){P(this._$AH)||(this._$AH=[],this._$AR());let n=this._$AH,r,i=0;for(let a of t)i===n.length?n.push(r=new e(this.O(M()),this.O(M()),this,this.options)):r=n[i],r._$AI(a),i++;i<n.length&&(this._$AR(r&&r._$AB.nextSibling,i),n.length=i)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){let t=T(e).nextSibling;T(e).remove(),e=t}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},W=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,n,r,i){this.type=1,this._$AH=B,this._$AN=void 0,this.element=e,this.name=t,this._$AM=r,this.options=i,n.length>2||n[0]!==``||n[1]!==``?(this._$AH=Array(n.length-1).fill(new String),this.strings=n):this._$AH=B}_$AI(e,t=this,n,r){let i=this.strings,a=!1;if(i===void 0)e=U(this,e,t,0),a=!N(e)||e!==this._$AH&&e!==z,a&&(this._$AH=e);else{let r=e,o,s;for(e=i[0],o=0;o<i.length-1;o++)s=U(this,r[n+o],t,o),s===z&&(s=this._$AH[o]),a||=!N(s)||s!==this._$AH[o],s===B?e=B:e!==B&&(e+=(s??``)+i[o+1]),this._$AH[o]=s}a&&!r&&this.j(e)}j(e){e===B?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??``)}},fe=class extends W{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===B?void 0:e}},pe=class extends W{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==B)}},me=class extends W{constructor(e,t,n,r,i){super(e,t,n,r,i),this.type=5}_$AI(e,t=this){if((e=U(this,e,t,0)??B)===z)return;let n=this._$AH,r=e===B&&n!==B||e.capture!==n.capture||e.once!==n.once||e.passive!==n.passive,i=e!==B&&(n===B||r);r&&this.element.removeEventListener(this.name,this,n),i&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH==`function`?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},he=class{constructor(e,t,n){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=n}get _$AU(){return this._$AM._$AU}_$AI(e){U(this,e)}},ge=w.litHtmlPolyfillSupport;ge?.(H,de),(w.litHtmlVersions??=[]).push(`3.3.3`);var _e=(e,t,n)=>{let r=n?.renderBefore??t,i=r._$litPart$;if(i===void 0){let e=n?.renderBefore??null;r._$litPart$=i=new de(t.insertBefore(M(),e),e,void 0,n??{})}return i._$AI(e),i},ve=globalThis,G=class extends C{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=_e(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return z}};G._$litElement$=!0,G.finalized=!0,ve.litElementHydrateSupport?.({LitElement:G});var ye=ve.litElementPolyfillSupport;ye?.({LitElement:G}),(ve.litElementVersions??=[]).push(`4.2.2`);var be=`unraid-server-card`,xe=`unraid-server-card-editor`,Se=`unraid-storage-card`,Ce=`unraid-storage-card-editor`,we=`unraid-docker-card`,Te=`unraid-docker-card-editor`,Ee=`unraid-ups-card`,De=`unraid-ups-card-editor`,Oe=`unraid-vm-card`,ke=`unraid-vm-card-editor`,Ae=`unraid-shares-card`,je=`unraid-shares-card-editor`,Me=`unraid-network-card`,Ne=`unraid-network-card-editor`,Pe=`unraid-dashboard-card`,Fe=`unraid-dashboard-card-editor`,Ie=[o`
  :host {
    --unraid-primary: var(--primary-color, #f25f22);
    --unraid-accent: #f25f22;
    --unraid-online: var(--success-color, #2ecc71);
    --unraid-warning: var(--warning-color, #f39c12);
    --unraid-error: var(--error-color, #e74c3c);
    --unraid-standby: var(--disabled-text-color, #7f8c8d);
    --unraid-info: var(--info-color, #3498db);
    --unraid-card-bg: var(--ha-card-background, var(--card-background-color, #1c1c20));
    --unraid-border: var(--ha-card-border-color, var(--divider-color, rgba(255, 255, 255, 0.08)));
    --unraid-radius: var(--ha-card-border-radius, 12px);
    --unraid-text: var(--primary-text-color, #e1e1e6);
    --unraid-subtext: var(--secondary-text-color, #8a8a93);
  }
`,o`
    :host {
      display: block;
      height: 100%;
      box-sizing: border-box;
    }

    ha-card {
      height: 100%;
      box-sizing: border-box;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      overflow: hidden;
      background: var(--unraid-card-bg);
      border: 1px solid var(--unraid-border);
      border-radius: var(--unraid-radius);
      color: var(--unraid-text);
      font-family: var(--ha-card-font-family, inherit);
    }

    :host([embedded]) ha-card {
      border: none;
      box-shadow: none;
      background: transparent;
      padding: 0;
    }

    .icon {
      display: inline-block;
      vertical-align: middle;
      fill: currentColor;
      flex-shrink: 0;
    }

    /* Header */
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }

    .header-main {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }

    .header-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: color-mix(in srgb, var(--unraid-accent) 15%, transparent);
      color: var(--unraid-accent);
      display: grid;
      place-items: center;
      flex-shrink: 0;
    }

    .header-titles {
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    .header-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--unraid-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1.25;
    }

    .header-subtitle {
      font-size: 0.78rem;
      color: var(--unraid-subtext);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }

    /* Badges / Chips */
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 0.72rem;
      font-weight: 600;
      line-height: 1;
      white-space: nowrap;
    }

    .badge-online {
      background: color-mix(in srgb, var(--unraid-online) 15%, transparent);
      color: var(--unraid-online);
      border: 1px solid color-mix(in srgb, var(--unraid-online) 25%, transparent);
    }

    .badge-warning {
      background: color-mix(in srgb, var(--unraid-warning) 15%, transparent);
      color: var(--unraid-warning);
      border: 1px solid color-mix(in srgb, var(--unraid-warning) 25%, transparent);
    }

    .badge-error {
      background: color-mix(in srgb, var(--unraid-error) 15%, transparent);
      color: var(--unraid-error);
      border: 1px solid color-mix(in srgb, var(--unraid-error) 25%, transparent);
    }

    .badge-standby {
      background: color-mix(in srgb, var(--unraid-standby) 15%, transparent);
      color: var(--unraid-standby);
      border: 1px solid color-mix(in srgb, var(--unraid-standby) 25%, transparent);
    }

    .pulse-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: currentColor;
    }

    /* Conic Ring Gauges */
    .rings-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(85px, 1fr));
      gap: 8px;
    }

    .ring-card {
      background: color-mix(in srgb, var(--unraid-text) 3%, transparent);
      border: 1px solid var(--unraid-border);
      border-radius: 10px;
      padding: 10px 6px;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 6px;
    }

    .ring-gauge {
      width: 54px;
      height: 54px;
      border-radius: 50%;
      position: relative;
      display: grid;
      place-items: center;
      background: conic-gradient(
        var(--ring-color, var(--unraid-primary)) calc(var(--pct, 0) * 1%),
        color-mix(in srgb, var(--unraid-text) 8%, transparent) 0
      );
      flex-shrink: 0;
    }

    .ring-gauge::after {
      content: "";
      position: absolute;
      inset: 6px;
      border-radius: 50%;
      background: var(--unraid-card-bg);
    }

    .ring-content {
      position: relative;
      z-index: 2;
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--unraid-text);
    }

    .ring-label {
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--unraid-text);
      line-height: 1.1;
    }

    .ring-subtext {
      font-size: 0.68rem;
      color: var(--unraid-subtext);
      line-height: 1.1;
      white-space: nowrap;
    }

    /* Progress Bars */
    .progress-bar {
      width: 100%;
      height: 6px;
      background: color-mix(in srgb, var(--unraid-text) 10%, transparent);
      border-radius: 4px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: var(--fill-color, var(--unraid-accent));
      border-radius: 4px;
      transition: width 0.3s ease;
    }

    /* Lists / Tables */
    .item-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .list-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      border-radius: 8px;
      background: color-mix(in srgb, var(--unraid-text) 3%, transparent);
      border: 1px solid var(--unraid-border);
      gap: 10px;
      font-size: 0.8rem;
      transition: border-color 0.2s ease;
    }

    .list-row:hover {
      border-color: color-mix(in srgb, var(--unraid-accent) 40%, transparent);
    }

    .row-left {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
      flex: 1;
    }

    .row-right {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 5px 12px;
      border-radius: 8px;
      font-size: 0.78rem;
      font-weight: 600;
      border: 1px solid var(--unraid-border);
      background: color-mix(in srgb, var(--unraid-text) 6%, transparent);
      color: var(--unraid-text);
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .btn:hover {
      background: color-mix(in srgb, var(--unraid-text) 12%, transparent);
    }

    .btn-primary {
      background: var(--unraid-accent);
      color: white;
      border-color: transparent;
    }

    .btn-primary:hover {
      filter: brightness(1.1);
    }

    .btn-icon {
      padding: 6px;
      border-radius: 6px;
      border: 1px solid transparent;
      background: transparent;
      color: var(--unraid-subtext);
      cursor: pointer;
    }

    .btn-icon:hover {
      background: color-mix(in srgb, var(--unraid-text) 8%, transparent);
      color: var(--unraid-text);
    }

    /* Docker Containers Grid View (like Unraid GUI) */
    .container-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
      gap: 8px;
    }

    .container-tile {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 10px;
      border-radius: 8px;
      background: color-mix(in srgb, var(--unraid-text) 4%, transparent);
      border: 1px solid var(--unraid-border);
      cursor: pointer;
      gap: 6px;
      transition: all 0.2s ease;
    }

    .container-tile:hover {
      border-color: var(--unraid-accent);
    }

    .tile-name {
      font-size: 0.76rem;
      font-weight: 600;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      min-width: 0;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    .status-dot.online {
      background: var(--unraid-online);
    }

    .status-dot.offline {
      background: var(--unraid-error);
      border-radius: 2px;
    }

    /* Section divider */
    .divider {
      height: 1px;
      background: var(--unraid-border);
      width: 100%;
      margin: 4px 0;
    }

    /* Details Rows */
    .detail-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 8px;
      font-size: 0.75rem;
    }

    .detail-item {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .detail-label {
      color: var(--unraid-subtext);
      font-size: 0.68rem;
    }

    .detail-val {
      font-weight: 600;
      color: var(--unraid-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    /* Tab strip for unified dashboard card */
    .tab-strip {
      display: flex;
      gap: 6px;
      overflow-x: auto;
      border-bottom: 1px solid var(--unraid-border);
      padding-bottom: 6px;
    }

    .tab-btn {
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.76rem;
      font-weight: 600;
      background: transparent;
      border: none;
      color: var(--unraid-subtext);
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s ease;
    }

    .tab-btn:hover {
      color: var(--unraid-text);
      background: color-mix(in srgb, var(--unraid-text) 5%, transparent);
    }

    .tab-btn.active {
      background: color-mix(in srgb, var(--unraid-accent) 15%, transparent);
      color: var(--unraid-accent);
    }
  `];function K(e,t,n,r){let i=new CustomEvent(t,{bubbles:r?.bubbles??!0,cancelable:!!r?.cancelable,composed:r?.composed??!0,detail:n});return e.dispatchEvent(i),i}var q=`M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z`,Le=`M12 2C6.5 2 2 6.5 2 12S6.5 22 12 22 22 17.5 22 12 17.5 2 12 2M10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z`,Re=`M21.81 10.25C21.75 10.21 21.25 9.82 20.17 9.82C19.89 9.82 19.61 9.85 19.33 9.9C19.12 8.5 17.95 7.79 17.9 7.76L17.61 7.59L17.43 7.86C17.19 8.22 17 8.63 16.92 9.05C16.72 9.85 16.84 10.61 17.25 11.26C16.76 11.54 15.96 11.61 15.79 11.61H2.62C2.28 11.61 2 11.89 2 12.24C2 13.39 2.18 14.54 2.58 15.62C3.03 16.81 3.71 17.69 4.58 18.23C5.56 18.83 7.17 19.17 9 19.17C9.79 19.17 10.61 19.1 11.42 18.95C12.54 18.75 13.62 18.36 14.61 17.79C15.43 17.32 16.16 16.72 16.78 16C17.83 14.83 18.45 13.5 18.9 12.35H19.09C20.23 12.35 20.94 11.89 21.33 11.5C21.59 11.26 21.78 10.97 21.92 10.63L22 10.39L21.81 10.25M3.85 11.24H5.61C5.69 11.24 5.77 11.17 5.77 11.08V9.5C5.77 9.42 5.7 9.34 5.61 9.34H3.85C3.76 9.34 3.69 9.41 3.69 9.5V11.08C3.7 11.17 3.76 11.24 3.85 11.24M6.28 11.24H8.04C8.12 11.24 8.2 11.17 8.2 11.08V9.5C8.2 9.42 8.13 9.34 8.04 9.34H6.28C6.19 9.34 6.12 9.41 6.12 9.5V11.08C6.13 11.17 6.19 11.24 6.28 11.24M8.75 11.24H10.5C10.6 11.24 10.67 11.17 10.67 11.08V9.5C10.67 9.42 10.61 9.34 10.5 9.34H8.75C8.67 9.34 8.6 9.41 8.6 9.5V11.08C8.6 11.17 8.66 11.24 8.75 11.24M11.19 11.24H12.96C13.04 11.24 13.11 11.17 13.11 11.08V9.5C13.11 9.42 13.05 9.34 12.96 9.34H11.19C11.11 9.34 11.04 9.41 11.04 9.5V11.08C11.04 11.17 11.11 11.24 11.19 11.24M6.28 9H8.04C8.12 9 8.2 8.91 8.2 8.82V7.25C8.2 7.16 8.13 7.09 8.04 7.09H6.28C6.19 7.09 6.12 7.15 6.12 7.25V8.82C6.13 8.91 6.19 9 6.28 9M8.75 9H10.5C10.6 9 10.67 8.91 10.67 8.82V7.25C10.67 7.16 10.61 7.09 10.5 7.09H8.75C8.67 7.09 8.6 7.15 8.6 7.25V8.82C8.6 8.91 8.66 9 8.75 9M11.19 9H12.96C13.04 9 13.11 8.91 13.11 8.82V7.25C13.11 7.16 13.04 7.09 12.96 7.09H11.19C11.11 7.09 11.04 7.15 11.04 7.25V8.82C11.04 8.91 11.11 9 11.19 9M11.19 6.72H12.96C13.04 6.72 13.11 6.65 13.11 6.56V5C13.11 4.9 13.04 4.83 12.96 4.83H11.19C11.11 4.83 11.04 4.89 11.04 5V6.56C11.04 6.64 11.11 6.72 11.19 6.72M13.65 11.24H15.41C15.5 11.24 15.57 11.17 15.57 11.08V9.5C15.57 9.42 15.5 9.34 15.41 9.34H13.65C13.57 9.34 13.5 9.41 13.5 9.5V11.08C13.5 11.17 13.57 11.24 13.65 11.24`,ze=`M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z`,Be=`M7,15H9V18H11V15H13V18H15V15H17V18H19V9H15V6H9V9H5V18H7V15M4.38,3H19.63C20.94,3 22,4.06 22,5.38V19.63A2.37,2.37 0 0,1 19.63,22H4.38C3.06,22 2,20.94 2,19.63V5.38C2,4.06 3.06,3 4.38,3Z`,Ve=`M7,2V13H10V22L17,10H13L17,2H7Z`,He=`M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z`,Ue=`M6,2H18A2,2 0 0,1 20,4V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V4A2,2 0 0,1 6,2M12,4A6,6 0 0,0 6,10C6,13.31 8.69,16 12.1,16L11.22,13.77C10.95,13.29 11.11,12.68 11.59,12.4L12.45,11.9C12.93,11.63 13.54,11.79 13.82,12.27L15.74,14.69C17.12,13.59 18,11.9 18,10A6,6 0 0,0 12,4M12,9A1,1 0 0,1 13,10A1,1 0 0,1 12,11A1,1 0 0,1 11,10A1,1 0 0,1 12,9M7,18A1,1 0 0,0 6,19A1,1 0 0,0 7,20A1,1 0 0,0 8,19A1,1 0 0,0 7,18M12.09,13.27L14.58,19.58L17.17,18.08L12.95,12.77L12.09,13.27Z`,We=`M4,1C2.89,1 2,1.89 2,3V7C2,8.11 2.89,9 4,9H1V11H13V9H10C11.11,9 12,8.11 12,7V3C12,1.89 11.11,1 10,1H4M4,3H10V7H4V3M3,13V18L3,20H10V18H5V13H3M14,13C12.89,13 12,13.89 12,15V19C12,20.11 12.89,21 14,21H11V23H23V21H20C21.11,21 22,20.11 22,19V15C22,13.89 21.11,13 20,13H14M14,15H20V19H14V15Z`,Ge=`M21,16H3V4H21M21,2H3C1.89,2 1,2.89 1,4V16A2,2 0 0,0 3,18H10V20H8V22H16V20H14V18H21A2,2 0 0,0 23,16V4C23,2.89 22.1,2 21,2Z`,Ke=`M14,19H18V5H14M6,19H10V5H6V19Z`,qe=`M8,5.14V19.14L19,12.14L8,5.14Z`,Je=`M16.56,5.44L15.11,6.89C16.84,7.94 18,9.83 18,12A6,6 0 0,1 12,18A6,6 0 0,1 6,12C6,9.83 7.16,7.94 8.88,6.88L7.44,5.44C5.36,6.88 4,9.28 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12C20,9.28 18.64,6.88 16.56,5.44M13,3H11V13H13`,Ye=`M12,4C14.1,4 16.1,4.8 17.6,6.3C20.7,9.4 20.7,14.5 17.6,17.6C15.8,19.5 13.3,20.2 10.9,19.9L11.4,17.9C13.1,18.1 14.9,17.5 16.2,16.2C18.5,13.9 18.5,10.1 16.2,7.7C15.1,6.6 13.5,6 12,6V10.6L7,5.6L12,0.6V4M6.3,17.6C3.7,15 3.3,11 5.1,7.9L6.6,9.4C5.5,11.6 5.9,14.4 7.8,16.2C8.3,16.7 8.9,17.1 9.6,17.4L9,19.4C8,19 7.1,18.4 6.3,17.6Z`,Xe=`M4,1H20A1,1 0 0,1 21,2V6A1,1 0 0,1 20,7H4A1,1 0 0,1 3,6V2A1,1 0 0,1 4,1M4,9H20A1,1 0 0,1 21,10V14A1,1 0 0,1 20,15H4A1,1 0 0,1 3,14V10A1,1 0 0,1 4,9M4,17H20A1,1 0 0,1 21,18V22A1,1 0 0,1 20,23H4A1,1 0 0,1 3,22V18A1,1 0 0,1 4,17M9,5H10V3H9V5M9,13H10V11H9V13M9,21H10V19H9V21M5,3V5H7V3H5M5,11V13H7V11H5M5,19V21H7V19H5Z`,Ze=`M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5M11,7H13V13H11M11,15H13V17H11`,Qe=`M10,17L6,13L7.41,11.59L10,14.17L16.59,7.58L18,9M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1Z`,$e=`M9,16V10H5L12,3L19,10H15V16H9M5,20V18H19V20H5Z`,et=`M8 15C8.55 15 9 15.45 9 16C9 16.55 8.55 17 8 17C7.45 17 7 16.55 7 16C7 15.45 7.45 15 8 15M15.07 4.69L16.5 6.1L15.07 7.5L13.66 6.1L15.07 4.69M17.9 7.5L19.31 8.93L17.9 10.34L16.5 8.93L17.9 7.5M8 13C6.34 13 5 14.34 5 16C5 17.66 6.34 19 8 19C9.66 19 11 17.66 11 16C11 14.34 9.66 13 8 13M9.77 4.33L10.5 5.08L14.29 1.29C14.47 1.11 14.72 1 15 1C15.28 1 15.53 1.11 15.71 1.29L22.78 8.36L22.78 8.37C22.92 8.54 23 8.76 23 9C23 9.3 22.87 9.57 22.66 9.76L22.66 9.76L18.93 13.5L19.67 14.23L12.95 20.95C11.68 22.22 9.93 23 8 23C4.13 23 1 19.87 1 16C1 14.07 1.78 12.32 3.05 11.05L9.77 4.33M20.59 9L15 3.41L11.93 6.5L17.5 12.08L20.59 9Z`,tt=`M3,11H11V3H3M3,21H11V13H3M13,21H21V13H13M13,3V11H21V3`,nt=`M9,5V9H21V5M9,19H21V15H9M9,14H21V10H9M4,9H8V5H4M4,19H8V15H4M4,14H8V10H4V14Z`;function J(e,t=20,n=`icon`){return R`
    <svg
      class="${n}"
      style="width: ${t}px; height: ${t}px;"
      viewBox="0 0 24 24"
    >
      <path d="${e}" fill="currentColor"></path>
    </svg>
  `}var Y=class extends G{static styles=Ie;static editorTag=``;static async getConfigElement(){return document.createElement(this.editorTag)}static properties={hass:{attribute:!1},config:{attribute:!1}};constructor(){super(),this.config={type:``}}willUpdate(e){super.willUpdate(e),e.has(`config`)&&(this.config.embedded?this.setAttribute(`embedded`,``):this.removeAttribute(`embedded`))}setConfig(e){if(!e||typeof e.type!=`string`)throw Error(`Invalid card configuration`);this.config={...e},this.config.embedded?this.setAttribute(`embedded`,``):this.removeAttribute(`embedded`)}getCardSize(){return 4}getGridOptions(){return{columns:6,rows:4,min_columns:3,min_rows:3}}getUnraidDevices(){return this.hass?.devices?Object.values(this.hass.devices).filter(e=>e.identifiers?.some(([e])=>e===`unraid`)):[]}getActiveDevice(){let e=this.getUnraidDevices();if(e.length!==0){if(this.config.server){let t=e.find(e=>e.id===this.config.server||e.name?.toLowerCase()===this.config.server?.toLowerCase()||e.name_by_user?.toLowerCase()===this.config.server?.toLowerCase());if(t)return t}return e[0]}}getEntity(e,t){if(!this.hass?.states)return;let n=this.getActiveDevice(),r=n?.id;if(this.hass.entities&&r){for(let n of Object.values(this.hass.entities))if(n.device_id===r&&n.translation_key===e&&(!t||n.entity_id.startsWith(`${t}.`))){let e=this.hass.states[n.entity_id];if(e)return e}}return Object.values(this.hass.states).find(r=>{if(t&&!r.entity_id.startsWith(`${t}.`))return!1;if(this.hass?.entities){let e=this.hass.entities[r.entity_id];if(e&&e.platform!==`unraid`)return!1}let i=r.entity_id.split(`.`)[1]||``,a=i.endsWith(`_${e}`)||i===e||e===`uptime`&&(i.endsWith(`_up_since`)||i===`up_since`)||e===`network_interface_ip`&&i.includes(`_network_`)&&(i.endsWith(`_ip`)||i.endsWith(`_ip_address`))||e===`network_access`&&i.endsWith(`_network_access`);if(n?.name){let e=n.name.toLowerCase().replace(/[^a-z0-9]/g,`_`);return a&&i.includes(e)}return a})}getNetworkInterfaces(){if(!this.hass?.states)return[];let e=this.getActiveDevice(),t=e?.name?e.name.toLowerCase().replace(/[^a-z0-9]/g,`_`):void 0,n=new Map;for(let[e,r]of Object.entries(this.hass.states)){if(t&&!e.includes(t))continue;let i=e.match(/_network_([a-zA-Z0-9_-]+)_(inbound(?:_throughput)?|outbound(?:_throughput)?|rx(?:_throughput)?|tx(?:_throughput)?|speed|ip|ip_address|link)$/i);if(!i||!i[1]||!i[2])continue;let a=i[1],o=i[2].toLowerCase();n.has(a)||n.set(a,{name:a,displayName:a.toUpperCase()});let s=n.get(a);o.startsWith(`inbound`)||o.startsWith(`rx`)?s.rx=r:o.startsWith(`outbound`)||o.startsWith(`tx`)?s.tx=r:o===`speed`?s.speed=r:o===`ip`||o===`ip_address`?s.ip=r:o===`link`&&(s.link=r)}return Array.from(n.values()).sort((e,t)=>e.name.localeCompare(t.name,void 0,{numeric:!0}))}getBootDiskEntity(){if(!this.hass?.states)return;let e=this.getActiveDevice(),t=e?.name?e.name.toLowerCase().replace(/[^a-z0-9]/g,`_`):void 0;return Object.values(this.hass.states).find(e=>!e.entity_id.startsWith(`sensor.`)||t&&!e.entity_id.includes(t)?!1:(e.entity_id.includes(`_disk_flash_`)||e.entity_id.includes(`_disk_boot_`))&&e.entity_id.endsWith(`_usage`))}getEntities(e,t){if(!this.hass?.states)return[];let n=this.getActiveDevice(),r=n?.id;if(this.hass.entities&&r){let n=[];for(let i of Object.values(this.hass.entities))if(i.device_id===r&&i.translation_key===e&&(!t||i.entity_id.startsWith(`${t}.`))){let e=this.hass.states[i.entity_id];e&&n.push(e)}if(n.length>0)return n}let i=n?.name?n.name.toLowerCase().replace(/[^a-z0-9]/g,`_`):void 0,a=t=>{if(this.hass?.entities){let e=this.hass.entities[t.entity_id];if(e&&e.platform!==`unraid`)return!1}if(e===`disk_usage`)return(t.entity_id.includes(`_disk_`)||t.entity_id.includes(`_cache`)||t.entity_id.includes(`_parity`)||t.entity_id.includes(`_boot`)||t.entity_id.includes(`_flash`))&&t.entity_id.endsWith(`_usage`)&&!t.entity_id.includes(`_array_usage`)&&!t.entity_id.includes(`_share_`);if(e===`disk_temperature`)return(t.entity_id.includes(`_disk_`)||t.entity_id.includes(`_cache`)||t.entity_id.includes(`_parity`)||t.entity_id.includes(`_boot`))&&(t.entity_id.endsWith(`_temperature`)||t.entity_id.includes(`_temp`));if(e===`disk_spin`)return(t.entity_id.includes(`_disk_`)||t.entity_id.includes(`_cache`)||t.entity_id.includes(`_parity`))&&t.entity_id.includes(`_spin`);if(e===`disk_health`)return(t.entity_id.includes(`_disk_`)||t.entity_id.includes(`_cache`)||t.entity_id.includes(`_parity`)||t.entity_id.includes(`_boot`))&&(t.entity_id.endsWith(`_health`)||t.entity_id.includes(`_health_`));if(e===`share_usage`||e===`share`)return t.entity_id.includes(`_share_`)&&t.entity_id.endsWith(`_usage`);let n=t.entity_id.split(`.`)[1]||``;return n===e||n.endsWith(`_${e}`)||n.includes(`_${e}_`)||n.startsWith(`${e}_`)},o=Object.values(this.hass.states),s=t?o.filter(e=>e.entity_id.startsWith(`${t}.`)):o;return i?s.filter(e=>e.entity_id.includes(i)&&a(e)):s.filter(e=>a(e))}findEntity(e){if(this.hass?.states)return typeof e==`string`?this.hass.states[e]:Object.values(this.hass.states).find(t=>e.test(t.entity_id))}async toggleEntity(e){if(!this.hass)return;let t=e.split(`.`)[0]||`homeassistant`;await this.hass.callService(t,`toggle`,{entity_id:e})}async pressButton(e){this.hass&&await this.hass.callService(`button`,`press`,{entity_id:e})}openMoreInfo(e){K(this,`hass-more-info`,{entityId:e})}renderHeader(e,t,n,r){return this.config.embedded||this.config.hide_header?B:R`
      <div class="header">
        <div class="header-main">
          <div class="header-icon">${J(n,22)}</div>
          <div class="header-titles">
            <span class="header-title">${e}</span>
            <span class="header-subtitle">${t}</span>
          </div>
        </div>
        ${r?R`<div class="header-actions">${r}</div>`:``}
      </div>
    `}},X=class extends G{static properties={hass:{attribute:!1},_config:{state:!0}};static styles=o`
    .card-config {
      display: flex;
      flex-direction: column;
      gap: 14px;
      padding: 8px 0;
      color: var(--primary-text-color, #fff);
      font-size: 0.9rem;
    }
    .form-row {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    label {
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--secondary-text-color, #aaa);
    }
    input[type="text"],
    select {
      padding: 8px 12px;
      border-radius: 6px;
      border: 1px solid var(--divider-color, rgba(255, 255, 255, 0.15));
      background: var(--card-background-color, #1e1e24);
      color: var(--primary-text-color, #fff);
      font-size: 0.85rem;
    }
    .checkbox-row {
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
    }
    .checkbox-row input {
      width: 16px;
      height: 16px;
      accent-color: var(--primary-color, #f25f22);
    }
  `;setConfig(e){this._config={...e}}_valueChanged(e,t){this._config&&(this._config={...this._config,[e]:t},K(this,`config-changed`,{config:this._config}))}render(){if(!this._config)return R``;let e=this.hass?.devices?Object.values(this.hass.devices).filter(e=>e.identifiers?.some(([e])=>e===`unraid`)):[];return R`
      <div class="card-config">
        <!-- Server Selector -->
        <div class="form-row">
          <label for="server">Unraid Server</label>
          ${e.length>0?R`
                <select
                  id="server"
                  @change=${e=>this._valueChanged(`server`,e.target.value)}
                >
                  ${(()=>{let t=this._config.server||e[0]?.id||``;return e.map(e=>R`
                        <option
                          value=${e.id}
                          ?selected=${e.id===t}
                        >
                          ${e.name_by_user||e.name||e.id}
                        </option>
                      `)})()}
                </select>
              `:R`
                <input
                  type="text"
                  id="server"
                  placeholder="Auto-detecting server..."
                  .value=${this._config.server||``}
                  @input=${e=>this._valueChanged(`server`,e.target.value)}
                />
              `}
        </div>

        <!-- Custom Title -->
        <div class="form-row">
          <label for="title">Custom Title (optional)</label>
          <input
            type="text"
            id="title"
            placeholder="Leave empty for default"
            .value=${this._config.title||``}
            @input=${e=>this._valueChanged(`title`,e.target.value)}
          />
        </div>

        <!-- Specific options for Docker Card -->
        ${this._config.type?.includes(`docker`)?R`
              <div class="form-row">
                <label for="view_mode">Default View Mode</label>
                <select
                  id="view_mode"
                  .value=${this._config.view_mode||`grid`}
                  @change=${e=>this._valueChanged(`view_mode`,e.target.value)}
                >
                  <option value="grid">Grid View (Icons & Status)</option>
                  <option value="list">List View (Detailed Table)</option>
                </select>
              </div>
            `:``}

        <!-- Toggles -->
        <label class="checkbox-row">
          <input
            type="checkbox"
            .checked=${this._config.show_system_info!==!1}
            @change=${e=>this._valueChanged(`show_system_info`,e.target.checked)}
          />
          <span>Show System Details</span>
        </label>
      </div>
    `}},rt=class extends X{},it=class extends X{},at=class extends X{},ot=class extends X{},st=class extends X{},ct=class extends X{},lt=class extends X{},ut=class extends X{};function dt(e,t){if(!customElements.get(e))try{customElements.define(e,t)}catch(n){if(n instanceof Error&&(n.name===`NotSupportedError`||n.message.includes(`already been registered`))){class n extends t{}customElements.define(e,n)}else throw n}}function Z(e){dt(e.tag,e.card),dt(e.editorTag,e.editor),window.customCards??=[],window.customCards.some(t=>t.type===e.tag)||window.customCards.push({type:e.tag,name:e.name,description:e.description,preview:!0,documentationURL:`https://github.com/ruaan-deysel/ha-unraid`})}Z({tag:be,editorTag:xe,card:class extends Y{static editorTag=xe;formatUptime(e){if(!e)return`Unknown`;let t=e.trim(),n=0;if(/^\d+(\.\d+)?$/.test(t))n=Math.floor(Number(t));else{let t=new Date(e);if(!isNaN(t.getTime()))n=Math.max(0,Math.floor((Date.now()-t.getTime())/1e3));else return e}let r=Math.floor(n/86400),i=Math.floor(n%86400/3600),a=Math.floor(n%3600/60);return r>0?`${r}d ${i}h`:i>0?`${i}h ${a}m`:`${a}m`}render(){let e=this.getActiveDevice(),t=this.config.title||e?.name_by_user||e?.name||`Unraid Server`,n=this.getEntity(`cpu_usage`),r=this.getEntity(`ram_usage`),i=this.getEntity(`array_usage`),a=this.getEntity(`array_state`),o=this.getEntity(`system_temperature`)||this.getEntity(`temperature_average`),s=this.getEntity(`cpu_power`),c=this.getEntity(`uptime`),l=this.getEntity(`notifications_unread_alert`),u=this.getEntity(`network_interface_ip`),d=Math.round(Number(n?.state)||0),f=Math.round(Number(r?.state)||0),p=Math.round(Number(i?.state)||0),m=a?.state?.toLowerCase()===`started`||a?.state===`Normal`,h=Number(l?.state)||0,g=n?.attributes?.cpu_model||(e?.model??`Multi-Core CPU`),_=r?.attributes?.used||``,v=r?.attributes?.total||``,y=i?.attributes?.capacity_used||``,b=i?.attributes?.capacity_total||``,x=this.getNetworkInterfaces(),S=x.length>0?x[0]:void 0,C=S?.speed?.state||S?.link?.attributes?.speed_mbps,w=C==null?void 0:Number(C),T=w?w>=1e3?`${w/1e3} Gbps`:`${w} Mbps`:``,E=S?.rx?.state?parseFloat(S.rx.state):NaN,D=S?.tx?.state?parseFloat(S.tx.state):NaN,O=isNaN(E)?``:E<.1?`${(E*1024).toFixed(0)} kB/s`:`${E.toFixed(2)} MB/s`,k=isNaN(D)?``:D<.1?`${(D*1024).toFixed(0)} kB/s`:`${D.toFixed(2)} MB/s`,ee=O&&k?`↓ ${O} • ↑ ${k}`:T||`Active`,A=this.getBootDiskEntity()?.attributes,j=A?.used||A?.fs_used,M=A?.total||A?.fs_size,N=A?.device,P=j&&M?`Flash (${j} / ${M})`:N?`Flash (${N})`:`Flash (USB)`,te=A?.filesystem?`Device: ${N||`USB`} • FS: ${A.filesystem}`:`USB Flash Boot Drive`,F=R`
      <span class="badge ${m?`badge-online`:`badge-error`}">
        <span class="pulse-dot"></span>
        <span>Array ${a?.state||(m?`Started`:`Stopped`)}</span>
      </span>
      ${h>0?R`
            <span class="badge badge-error">
              ${J(q,13)}
              <span>${h}</span>
            </span>
          `:B}
    `;return R`
      <ha-card>
        ${this.renderHeader(t,`${e?.model||`Unraid OS`} • Up ${this.formatUptime(c?.state)}`,Xe,F)}

        <!-- Conic Ring Gauges -->
        <div class="rings-grid">
          <!-- CPU -->
          <div class="ring-card">
            <div
              class="ring-gauge"
              style="--pct: ${d}; --ring-color: ${d>80?`var(--unraid-error)`:d>50?`var(--unraid-warning)`:`var(--unraid-online)`}"
            >
              <span class="ring-content">${d}%</span>
            </div>
            <span class="ring-label">CPU Load</span>
            <span class="ring-subtext">
              ${o?.state?`${o.state}°C`:``}${s?.state?` • ${s.state}W`:``}
            </span>
          </div>

          <!-- RAM -->
          <div class="ring-card">
            <div
              class="ring-gauge"
              style="--pct: ${f}; --ring-color: ${f>85?`var(--unraid-error)`:`var(--unraid-info)`}"
            >
              <span class="ring-content">${f}%</span>
            </div>
            <span class="ring-label">Memory</span>
            <span class="ring-subtext">${_&&v?`${_} / ${v}`:`${f}% used`}</span>
          </div>

          <!-- Array -->
          <div class="ring-card">
            <div
              class="ring-gauge"
              style="--pct: ${p}; --ring-color: var(--unraid-accent)"
            >
              <span class="ring-content">${p}%</span>
            </div>
            <span class="ring-label">Array Storage</span>
            <span class="ring-subtext">${y&&b?`${y} / ${b}`:`${p}% used`}</span>
          </div>
        </div>

        ${this.config.show_system_info===!1?B:R`
              <div class="divider"></div>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="detail-label">Processor</span>
                  <span class="detail-val" title="${g}">${g}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">OS Version</span>
                  <span class="detail-val">${e?.sw_version||`Unraid OS`}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">System Uptime</span>
                  <span class="detail-val">${this.formatUptime(c?.state)}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Primary Network</span>
                  <span class="detail-val" title="${S?`${S.name} • ${T}`:`Connected`}">
                    ${S?`${S.name}: `:``}${S?.ip?.state||u?.state||`Connected`}
                  </span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Network Traffic</span>
                  <span class="detail-val" title="${T?`Link Speed: ${T}`:`Network Speed`}">${ee}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Boot Device</span>
                  <span class="detail-val" title="${te}">${P}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">System Health</span>
                  <span class="detail-val" style="color: ${h===0?`var(--unraid-online)`:`var(--unraid-error)`}">
                    ${h===0?`Normal • Healthy`:`${h} Active Alerts`}
                  </span>
                </div>
              </div>
            `}
      </ha-card>
    `}},editor:rt,name:`Unraid Server Overview Card`,description:`Server metrics, CPU/RAM ring gauges, and hardware health.`});function ft(e,t){let n=e.trim(),r=n.match(/^(?:.*?\s+)?(?:Disk\s+)?([a-zA-Z0-9_-]+)(?:\s+(?:usage|health|temperature|temp|spin|errors))?$/i);if(r&&r[1]){let e=r[1],t=e.match(/^disk[_\s]?(\d+)$/i);if(t)return`Disk ${t[1]}`;if(/^\d+$/.test(e))return`Disk ${e}`;if(e.toLowerCase()===`parity`)return`Parity`;let n=e.match(/^parity[_\s]?(\d+)$/i);return n?`Parity ${n[1]}`:e.toLowerCase()===`cache`?`Cache`:e.toLowerCase().startsWith(`cache_`)?`Cache (${e.slice(6).toUpperCase()})`:e.toLowerCase()===`boot`||e.toLowerCase()===`flash`?`Flash (Boot)`:e.replace(/\b\w/g,e=>e.toUpperCase())}return n||t}function Q(e){let t=(e.split(`.`)[1]||``).replace(/^.*?_disk_/,``).replace(/_usage$|_temperature$|_temp$|_errors$|_health$|_spin$/,``).toLowerCase().replace(/_/g,``),n=t.match(/^(?:disk)?(\d+)$/);return n?`disk${n[1]}`:t}Z({tag:Se,editorTag:Ce,card:class extends Y{static editorTag=Ce;getDisks(){let e=this.getEntities(`disk_usage`),t=this.getEntities(`disk_health`,`binary_sensor`),n=this.getEntities(`disk_temperature`),r=this.getEntities(`disk_error_count`),i=this.getEntities(`disk_spin`,`switch`),a=new Map;for(let t of e){let e=Q(t.entity_id),n=ft(t.attributes.friendly_name||e,e),r=n.toLowerCase().includes(`parity`),i=n.toLowerCase().includes(`cache`)||n.toLowerCase().includes(`pool`),o=n.toLowerCase().includes(`boot`)||n.toLowerCase().includes(`flash`),s=t.attributes.spin_state===`active`||t.attributes.spinning===!0,c=t.attributes.temperature_celsius??t.attributes.temperature,l=Number(t.attributes.num_errors??0),u=t.attributes.status||`DISK_OK`;a.set(e,{id:e,name:n,isParity:r,isCache:i,isBoot:o,usagePct:Math.round(Number(t.state)||0),temp:c==null?`*`:`${c}°C`,tempNum:typeof c==`number`?c:void 0,errors:l,health:`healthy`,statusText:u,isSpinning:s,freeSpace:t.attributes.free,totalSpace:t.attributes.total})}for(let e of t){let t=Q(e.entity_id);if(a.has(t)||t.includes(`disabled`)||t.includes(`missing`)||t.includes(`invalid`))continue;let n=ft(e.attributes.friendly_name||t,t),r=n.toLowerCase().includes(`parity`),i=n.toLowerCase().includes(`cache`),o=n.toLowerCase().includes(`boot`),s=e.attributes.spinning===!0||e.attributes.standby!==void 0&&!e.attributes.standby,c=e.attributes.temperature,l=e.attributes.status||`DISK_OK`;a.set(t,{id:t,name:n,isParity:r,isCache:i,isBoot:o,usagePct:0,temp:c==null?`*`:`${c}°C`,tempNum:typeof c==`number`?c:void 0,errors:0,health:e.state===`on`?`error`:`healthy`,statusText:l,isSpinning:s})}for(let e of n){let t=Q(e.entity_id),n=a.get(t);n&&e.state!==`unavailable`&&e.state!==`unknown`&&(n.temp=`${e.state}°C`,n.tempNum=parseFloat(e.state))}for(let e of r){let t=Q(e.entity_id),n=a.get(t);if(n){let t=Number(e.state);isNaN(t)||(n.errors=t)}}for(let e of i){let t=Q(e.entity_id),n=a.get(t);n&&(n.isSpinning=e.state===`on`,n.spinEntityId=e.entity_id)}for(let e of t){let t=Q(e.entity_id),n=a.get(t);n&&(e.attributes.status&&(n.statusText=e.attributes.status),e.attributes.spinning===void 0?e.attributes.standby!==void 0&&(n.isSpinning=!e.attributes.standby):n.isSpinning=!!e.attributes.spinning,e.attributes.temperature!==void 0&&n.temp===`*`&&(n.temp=`${e.attributes.temperature}°C`,n.tempNum=Number(e.attributes.temperature)),e.state===`on`&&(n.health=`error`))}for(let e of a.values()){let t=(e.statusText||``).toUpperCase(),n=t.includes(`ERR`)||t.includes(`WRONG`)||t.includes(`INVALID`)||t.includes(`DSBL`)||t.includes(`FAIL`);e.health=e.health===`error`||n||e.errors>=10?`error`:e.errors>0||e.tempNum!==void 0&&e.tempNum>45?`warning`:`healthy`}return Array.from(a.values()).sort((e,t)=>e.isParity===t.isParity?e.isBoot===t.isBoot?e.isCache===t.isCache?e.name.localeCompare(t.name,void 0,{numeric:!0}):e.isCache?1:-1:e.isBoot?1:-1:e.isParity?-1:1)}render(){let e=this.getEntity(`array_usage`),t=this.getEntity(`parity_status`),n=this.getEntity(`parity_progress`),r=this.getEntity(`parity_check`,`switch`),i=this.getEntity(`last_parity_check_date`),a=this.getEntity(`last_parity_check_errors`),o=Math.round(Number(e?.state)||0),s=e?.attributes?.capacity_used||``,c=e?.attributes?.capacity_total||``,l=e?.attributes?.capacity_free||``,u=n&&!isNaN(Number(n.state))&&Number(n.state)>0,d=Math.round(Number(n?.state)||0),f=t?.state?.toLowerCase()===`on`||t?.state?.toLowerCase()===`ok`||t?.state===`Valid`,p=this.getDisks(),m=R`
      <span class="badge ${f?`badge-online`:`badge-warning`}">
        ${J(f?Qe:Ze,13)}
        <span>${f?`Parity Valid`:`Parity Check Needed`}</span>
      </span>
    `;return R`
      <ha-card>
        ${this.renderHeader(this.config.title||`Storage Array & Disks`,`${s||`${o}%`} used of ${c||`Array`}${l?` (${l} Free)`:``}`,Ue,m)}

        <!-- Array Capacity Bar -->
        <div style="display: flex; flex-direction: column; gap: 4px;">
          <div style="display: flex; justify-content: space-between; font-size: 0.76rem; font-weight: 600;">
            <span>Array Capacity</span>
            <span>${o}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: ${o}%;"></div>
          </div>
        </div>

        <!-- Parity Check Status & Action Banner -->
        <div class="list-row" style="background: color-mix(in srgb, var(--unraid-text) 5%, transparent);">
          <div class="row-left">
            <div style="color: ${f?`var(--unraid-online)`:`var(--unraid-warning)`}">
              ${J(f?Le:q,18)}
            </div>
            <div style="display: flex; flex-direction: column; min-width: 0;">
              <span style="font-weight: 600; font-size: 0.78rem;">
                ${u?`Parity Check In Progress (${d}%)`:`Parity Status: ${f?`Valid`:`Check Needed`}`}
              </span>
              <span style="font-size: 0.7rem; color: var(--unraid-subtext);">
                ${i?.state?`Last check: ${i.state}`:`Parity healthy`}
                ${a?.state&&a.state!==`0`?` • ${a.state} errors`:``}
              </span>
            </div>
          </div>
          <div class="row-right">
            ${r?R`
                  <button
                    class="btn ${u?`btn`:`btn-primary`}"
                    @click=${()=>this.toggleEntity(r.entity_id)}
                  >
                    ${J(u?Ke:qe,14)}
                    <span>${u?`Cancel`:`Check Now`}</span>
                  </button>
                `:B}
          </div>
        </div>

        <!-- Disk Trays List -->
        <div class="item-list">
          ${p.length>0?p.map(e=>{let t=e.tempNum??parseFloat(e.temp),n=e.isSpinning&&!isNaN(t)&&e.temp!==`*`&&e.temp!==`unavailable`,r=n?t>45?`var(--unraid-error)`:t>36?`var(--unraid-warning)`:`var(--unraid-online)`:`var(--unraid-standby)`,i=n?`${Math.round(t)}°C`:`--`,a=e.health===`healthy`?R`
                      <span class="badge badge-online" style="font-size: 0.68rem; gap: 4px;">
                        ${J(Le,11)}
                        <span>Healthy</span>
                      </span>
                    `:e.health===`warning`?R`
                      <span class="badge badge-warning" style="font-size: 0.68rem; gap: 4px;">
                        ${J(q,11)}
                        <span>Warning${e.errors>0?` (${e.errors})`:``}</span>
                      </span>
                    `:R`
                      <span class="badge badge-error" style="font-size: 0.68rem; gap: 4px;">
                        ${J(q,11)}
                        <span>Error${e.errors>0?` (${e.errors})`:``}</span>
                      </span>
                    `;return R`
                  <div class="list-row">
                    <div class="row-left">
                      <!-- Spin status button or USB Flash badge -->
                      ${e.isBoot?R`
                            <span
                              class="badge badge-online"
                              style="font-size: 0.68rem; gap: 4px; min-width: 60px; justify-content: center;"
                              title="USB Flash Boot Drive"
                            >
                              ${J(et,11)}
                              <span>Flash</span>
                            </span>
                          `:e.spinEntityId?R`
                            <button
                              class="badge ${e.isSpinning?`badge-online`:`badge-standby`}"
                              style="cursor: pointer; border: none;"
                              title="Click to spin ${e.isSpinning?`down`:`up`}"
                              @click=${()=>this.toggleEntity(e.spinEntityId)}
                            >
                              <span class="status-dot ${e.isSpinning?`online`:`offline`}"></span>
                              <span>${e.isSpinning?`Active`:`Standby`}</span>
                            </button>
                          `:R`
                            <span class="badge ${e.isSpinning?`badge-online`:`badge-standby`}">
                              <span>${e.isSpinning?`Active`:`Standby`}</span>
                            </span>
                          `}

                      <span style="font-weight: 600; min-width: 75px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${e.name}
                      </span>
                    </div>

                    <div class="row-right">
                      <!-- Temperature Chip -->
                      <span
                        class="badge"
                        style="color: ${e.isBoot?`var(--unraid-text-dim)`:r}; background: color-mix(in srgb, ${e.isBoot?`var(--unraid-text-dim)`:r} 12%, transparent); min-width: 44px; justify-content: center;"
                        title="${e.isBoot?`USB Flash Drive`:e.isSpinning?`Temperature: ${i}`:`Disk is in standby`}"
                      >
                        ${e.isBoot?`--`:i}
                      </span>

                      <!-- Health Status (Healthy, Warning, Error) -->
                      ${a}

                      <!-- Utilization -->
                      <div style="display: flex; align-items: center; gap: 6px; width: 85px;">
                        ${e.isParity?R`
                              <span style="font-size: 0.72rem; color: var(--unraid-online); font-weight: 500; font-family: monospace;">
                                Parity
                              </span>
                            `:R`
                              <div class="progress-bar" style="height: 4px; flex: 1;">
                                <div
                                  class="progress-fill"
                                  style="width: ${e.usagePct}%; background: ${e.isBoot?`var(--unraid-warning)`:e.isCache?`var(--unraid-info)`:`var(--unraid-accent)`};"
                                ></div>
                              </div>
                              <span style="font-size: 0.7rem; font-family: monospace; color: var(--unraid-subtext);">
                                ${e.usagePct}%
                              </span>
                            `}
                      </div>
                    </div>
                  </div>
                `}):R`<div style="text-align: center; color: var(--unraid-subtext); font-size: 0.8rem; padding: 12px;">No disk devices found</div>`}
        </div>
      </ha-card>
    `}},editor:it,name:`Unraid Storage & Disks Card`,description:`Array capacity, parity checks, and interactive disk tray with spin state controls.`});function pt(e,t){let n=e.trim(),r=n.match(/^(?:.*?\s+)?Share\s+(.+?)(?:\s+usage)?$/i);return r&&r[1]?r[1].trim():(n=n.replace(/\s+usage$/i,``).replace(/_usage$/i,``).replace(/\s+share$/i,``).replace(/_share$/i,``).trim(),n||t)}Z({tag:Ae,editorTag:je,card:class extends Y{static editorTag=je;static properties={...Y.properties,_searchQuery:{state:!0}};constructor(){super(),this._searchQuery=``}getShares(){let e=this.getEntities(`share_usage`),t=[];for(let n of e){let e=(n.entity_id.split(`.`)[1]||``).replace(/^.*?_share_/,``).replace(/_usage$/,``),r=pt(n.attributes.friendly_name||e,e),i=n.attributes.color||``,a=i===`green-on`;t.push({id:e,name:r,entityId:n.entity_id,usagePct:Math.min(100,Math.max(0,Math.round(Number(n.state)||0))),used:n.attributes.used||``,total:n.attributes.total||``,free:n.attributes.free||``,isProtected:a,color:i,allocator:n.attributes.allocator})}return t.sort((e,t)=>e.name.localeCompare(t.name,void 0,{numeric:!0}))}_openMoreInfo(e){K(this,`hass-more-info`,{entityId:e})}render(){let e=this.getShares(),t=this._searchQuery?e.filter(e=>e.name.toLowerCase().includes(this._searchQuery.toLowerCase())):e,n=e.filter(e=>e.isProtected).length,r=e.length-n,i=R`
      <span class="badge ${r===0?`badge-online`:`badge-warning`}">
        ${J(r===0?Qe:Ze,13)}
        <span>${n} Protected${r>0?` • ${r} Unprotected`:``}</span>
      </span>
    `;return R`
      <ha-card>
        ${this.renderHeader(this.config.title||`User Shares`,`${e.length} configured shares`,He,i)}

        <!-- Search Bar if more than 4 shares -->
        ${e.length>4?R`
              <div style="margin-bottom: 4px;">
                <input
                  type="text"
                  placeholder="Filter shares..."
                  style="
                    width: 100%;
                    padding: 6px 10px;
                    border-radius: 6px;
                    border: 1px solid var(--unraid-border);
                    background: color-mix(in srgb, var(--unraid-text) 4%, transparent);
                    color: var(--unraid-text);
                    font-size: 0.8rem;
                    box-sizing: border-box;
                  "
                  .value=${this._searchQuery}
                  @input=${e=>this._searchQuery=e.target.value}
                />
              </div>
            `:B}

        <!-- Shares List -->
        <div class="item-list">
          ${t.length>0?t.map(e=>{let t=e.usagePct>90?`var(--unraid-error)`:e.usagePct>75?`var(--unraid-warning)`:`var(--unraid-online)`;return R`
                  <div
                    class="list-row"
                    style="cursor: pointer;"
                    title="Click for details on ${e.name}"
                    @click=${()=>this._openMoreInfo(e.entityId)}
                  >
                    <div class="row-left">
                      <!-- Folder Icon -->
                      <div
                        style="color: ${e.isProtected?`var(--unraid-accent)`:`var(--unraid-warning)`}; display: flex; align-items: center;"
                      >
                        ${J(He,18)}
                      </div>

                      <div style="display: flex; flex-direction: column; min-width: 0;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                          <span
                            style="font-weight: 600; font-size: 0.82rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"
                          >
                            ${e.name}
                          </span>

                          <!-- Protection Tag -->
                          <span
                            class="badge ${e.isProtected?`badge-online`:`badge-warning`}"
                            style="font-size: 0.62rem; padding: 1px 6px;"
                            title="${e.isProtected?`Data protected on parity array`:`Data on pool / unprotected storage`}"
                          >
                            ${e.isProtected?`Protected`:`Unprotected`}
                          </span>
                        </div>

                        ${e.used&&e.total?R`<span style="font-size: 0.7rem; color: var(--unraid-subtext);">${e.used} / ${e.total}${e.free?` • ${e.free} free`:``}</span>`:B}
                      </div>
                    </div>

                    <div class="row-right">
                      <!-- Utilization bar and percentage -->
                      <div style="display: flex; align-items: center; gap: 6px; width: 110px;">
                        <div class="progress-bar" style="height: 6px; flex: 1;">
                          <div
                            class="progress-fill"
                            style="width: ${e.usagePct}%; background: ${t};"
                          ></div>
                        </div>
                        <span
                          style="font-size: 0.72rem; font-family: monospace; font-weight: 600; color: var(--unraid-text); min-width: 32px; text-align: right;"
                        >
                          ${e.usagePct}%
                        </span>
                      </div>
                    </div>
                  </div>
                `}):R`
                <div style="text-align: center; color: var(--unraid-subtext); font-size: 0.8rem; padding: 16px;">
                  ${e.length===0?`No user shares found`:`No shares matching filter`}
                </div>
              `}
        </div>
      </ha-card>
    `}},editor:at,name:`Unraid User Shares Card`,description:`User share storage utilization, capacity allocation, and parity protection status.`}),Z({tag:Me,editorTag:Ne,card:class extends Y{static editorTag=Ne;formatDataRate(e,t=`MB/s`){if(!e)return`--`;let n=parseFloat(e);return isNaN(n)?e:n<=0?`0 kB/s`:n<.1?`${(n*1e3).toFixed(1)} kB/s`:`${n.toFixed(2)} ${t}`}isValidIp(e){return!!e&&![`unavailable`,`unknown`,`none`,`--`].includes(e.toLowerCase().trim())}formatSpeed(e){if(!e)return``;let t=Number(e);return isNaN(t)?e:t>=1e3?`${t/1e3} Gbps`:`${t} Mbps`}handleMoreInfo(e){e&&K(this,`hass-more-info`,{entityId:e})}render(){let e=this.getActiveDevice(),t=this.config.title||e?.name_by_user||e?.name||`Unraid Server`,n=this.getNetworkInterfaces(),r=this.getEntity(`network_access`),i=r?.attributes,a=i?.LAN_IPv4_ipv4||(r?.state?.startsWith(`http`)?r.state:void 0),o=i?.FQDN_LAN_ipv4,s=n.filter(e=>e.link?.state===`on`||this.isValidIp(e.ip?.state)).length,c=R`
      <span class="badge ${s>0?`badge-online`:`badge-error`}">
        <span class="pulse-dot"></span>
        <span>${s} Connected</span>
      </span>
    `;return R`
      <ha-card>
        ${this.renderHeader(this.config.title||`${t} Network`,`${e?.model||`Unraid`} • ${n.length} Interface${n.length===1?``:`s`}`,We,c)}

        <!-- Interfaces List -->
        <div class="item-list">
          ${n.length>0?n.map(e=>{let t=e.link?.state===`on`||this.isValidIp(e.ip?.state),n=this.isValidIp(e.ip?.state)?e.ip.state:`--`,r=e.ip?.attributes?.mac_address||e.link?.attributes?.mac_address||``,i=e.link?.attributes?.mtu||e.ip?.attributes?.mtu||void 0,a=e.speed?.state||e.link?.attributes?.speed_mbps,o=this.formatSpeed(a==null?void 0:String(a)),s=this.formatDataRate(e.rx?.state),c=this.formatDataRate(e.tx?.state),l=e.rx?.attributes?.total_received||``,u=e.tx?.attributes?.total_sent||``,d=e.ip?.entity_id||e.rx?.entity_id||e.link?.entity_id;return R`
                  <div
                    class="list-row"
                    style="cursor: pointer; flex-direction: column; align-items: stretch; gap: 8px; padding: 12px 14px;"
                    @click=${()=>this.handleMoreInfo(d)}
                  >
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                      <div class="row-left" style="gap: 8px;">
                        <span class="badge ${t?`badge-online`:`badge-error`}" style="min-width: 50px; justify-content: center;">
                          ${J(Be,13)}
                          <span>${e.name}</span>
                        </span>
                        <span style="font-weight: 600; font-size: 0.88rem;">
                          ${n}
                        </span>
                      </div>

                      <div class="row-right" style="gap: 6px;">
                        ${o?R`
                              <span
                                class="badge"
                                style="color: var(--unraid-info); background: color-mix(in srgb, var(--unraid-info) 12%, transparent); font-weight: 600; font-size: 0.72rem;"
                              >
                                ${o}
                              </span>
                            `:B}
                        <span
                          class="badge ${t?`badge-online`:`badge-standby`}"
                          style="font-size: 0.68rem;"
                        >
                          ${t?`Up`:`Down`}
                        </span>
                      </div>
                    </div>

                    <!-- Throughput and Addressing details -->
                    <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.75rem; color: var(--unraid-subtext); border-top: 1px solid var(--unraid-border, rgba(255,255,255,0.06)); padding-top: 6px;">
                      <div style="display: flex; align-items: center; gap: 14px;">
                        <span style="display: flex; align-items: center; gap: 4px;" title="${l?`Total Inbound: ${l}`:`Inbound Transfer Rate`}">
                          <span style="color: var(--unraid-online);">${J(ze,13)}</span>
                          <span style="font-family: monospace; font-weight: 500;">${s}</span>
                          ${l?R`<span style="opacity: 0.7; font-size: 0.68rem;">(${l})</span>`:B}
                        </span>

                        <span style="display: flex; align-items: center; gap: 4px;" title="${u?`Total Outbound: ${u}`:`Outbound Transfer Rate`}">
                          <span style="color: var(--unraid-info);">${J($e,13)}</span>
                          <span style="font-family: monospace; font-weight: 500;">${c}</span>
                          ${u?R`<span style="opacity: 0.7; font-size: 0.68rem;">(${u})</span>`:B}
                        </span>
                      </div>

                      <div style="display: flex; align-items: center; gap: 8px; opacity: 0.8; font-size: 0.7rem;">
                        ${i?R`<span>MTU ${i}</span>`:B}
                        ${r?R`<span style="font-family: monospace;">${r}</span>`:B}
                      </div>
                    </div>
                  </div>
                `}):R`
                <div class="empty-state">
                  No network interfaces discovered for this server.
                </div>
              `}
        </div>

        ${a||o?R`
              <div class="divider"></div>
              <div class="detail-grid">
                ${a?R`
                      <div class="detail-item">
                        <span class="detail-label">LAN WebGUI</span>
                        <a
                          href="${a}"
                          target="_blank"
                          rel="noreferrer"
                          class="detail-val"
                          style="color: var(--unraid-accent); text-decoration: none;"
                        >
                          ${a}
                        </a>
                      </div>
                    `:B}
                ${o?R`
                      <div class="detail-item">
                        <span class="detail-label">Remote Access URL</span>
                        <a
                          href="${o}"
                          target="_blank"
                          rel="noreferrer"
                          class="detail-val"
                          style="color: var(--unraid-info); text-decoration: none;"
                        >
                          Connect FQDN
                        </a>
                      </div>
                    `:B}
              </div>
            `:B}
      </ha-card>
    `}},editor:ot,name:`Unraid Network Card`,description:`Network interfaces, link speeds, live throughput, and IP addresses.`});function $(e){let t=e.split(`.`)[1]||``;return t.replace(/^.*?_container_restart_/,``).replace(/^.*?_docker_container_restart_/,``).replace(/^.*?_container_autostart_/,``).replace(/^.*?_docker_container_autostart_/,``).replace(/^.*?_container_update_/,``).replace(/^.*?_docker_container_update_/,``).replace(/^.*?_docker_container_/,``).replace(/^.*?_container_switch_/,``).replace(/^docker_container_/,``).replace(/^container_switch_/,``).replace(/_cpu$/,``).replace(/_memory_usage$/,``).replace(/_memory$/,``).replace(/_docker_container$/,``).replace(/_container_switch$/,``).replace(/^.*?_container_/,``)||t}Z({tag:we,editorTag:Te,card:class extends Y{static editorTag=Te;static properties={...Y.properties,_filter:{state:!0},_viewMode:{state:!0}};constructor(){super(),this._filter=`all`,this._viewMode=`grid`}willUpdate(e){super.willUpdate(e),e.has(`config`)&&this.config.view_mode&&e.get(`config`)?.view_mode!==this.config.view_mode&&(this._viewMode=this.config.view_mode)}handleToggle(e,t,n){(!t||confirm(`Are you sure you want to stop container "${n}"?`))&&this.toggleEntity(e)}getContainers(){let e=this.getEntities(`docker_container_autostart`,`switch`),t=new Set(e.map(e=>e.entity_id)),n=this.getEntities(`docker_container`,`switch`).filter(e=>!t.has(e.entity_id)),r=this.getEntities(`docker_container_restart`,`button`),i=this.getEntities(`container_cpu`),a=this.getEntities(`container_memory_usage`),o=this.getEntities(`docker_container_update`,`update`),s=[];for(let t of n){let n=$(t.entity_id),c=t.attributes.friendly_name||n,l=t.state===`on`,u=r.find(e=>$(e.entity_id)===n),d=e.find(e=>$(e.entity_id)===n),f=i.find(e=>$(e.entity_id)===n),p=a.find(e=>$(e.entity_id)===n),m=o.find(e=>$(e.entity_id)===n);s.push({id:n,name:c,isRunning:l,switchEntityId:t.entity_id,restartEntityId:u?.entity_id,autostartEntityId:d?.entity_id,cpuPct:f?.state&&Number.isFinite(parseFloat(f.state))?parseFloat(f.state):void 0,memoryUsage:p?.state&&p.state!==`unavailable`?`${p.state} ${p.attributes.unit_of_measurement||`B`}`:void 0,hasUpdate:m?.state===`on`,updateEntityId:m?.entity_id})}return s.sort((e,t)=>e.isRunning&&!t.isRunning?-1:!e.isRunning&&t.isRunning?1:e.name.localeCompare(t.name))}render(){let e=this.getContainers(),t=e.filter(e=>e.isRunning).length,n=e.length-t,r=e.filter(e=>e.hasUpdate).length,i=this.getEntity(`check_container_updates`,`button`),a=e.filter(e=>this._filter===`running`?e.isRunning:this._filter===`stopped`?!e.isRunning:this._filter!==`updates`||e.hasUpdate),o=R`
      <span class="badge ${t>0?`badge-online`:`badge-standby`}">
        ${t} Running
      </span>
      ${r>0?R`
            <span class="badge badge-warning">
              ${J(q,12)}
              <span>${r} Updates</span>
            </span>
          `:B}
    `;return R`
      <ha-card>
        ${this.renderHeader(this.config.title||`Docker Containers`,`${t} running • ${n} stopped`,Re,o)}

        <!-- Top Controls & Filter Bar -->
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;">
          <div style="display: flex; gap: 4px; overflow-x: auto;">
            <button
              class="tab-btn ${this._filter===`all`?`active`:``}"
              @click=${()=>this._filter=`all`}
            >
              All (${e.length})
            </button>
            <button
              class="tab-btn ${this._filter===`running`?`active`:``}"
              @click=${()=>this._filter=`running`}
            >
              Running (${t})
            </button>
            <button
              class="tab-btn ${this._filter===`stopped`?`active`:``}"
              @click=${()=>this._filter=`stopped`}
            >
              Stopped (${n})
            </button>
            ${r>0?R`
                  <button
                    class="tab-btn ${this._filter===`updates`?`active`:``}"
                    style="color: var(--unraid-warning);"
                    @click=${()=>this._filter=`updates`}
                  >
                    Updates (${r})
                  </button>
                `:B}
          </div>

          <div style="display: flex; align-items: center; gap: 6px;">
            ${i?R`
                  <button
                    class="btn"
                    title="Check for updates"
                    @click=${()=>this.pressButton(i.entity_id)}
                  >
                    Check Updates
                  </button>
                `:B}
            <button
              class="btn-icon"
              title="Toggle View Mode"
              @click=${()=>this._viewMode=this._viewMode===`grid`?`list`:`grid`}
            >
              ${J(this._viewMode===`grid`?nt:tt,18)}
            </button>
          </div>
        </div>

        <!-- Containers Display (Grid or List View) -->
        ${this._viewMode===`grid`?R`
              <div class="container-grid">
                ${a.map(e=>R`
                    <div
                      class="container-tile"
                      @click=${()=>this.openMoreInfo(e.switchEntityId)}
                    >
                      <div style="display: flex; align-items: center; gap: 8px; min-width: 0;">
                        <span class="status-dot ${e.isRunning?`online`:`offline`}"></span>
                        <span class="tile-name" title="${e.name}">${e.name}</span>
                      </div>
                      <div style="display: flex; align-items: center; gap: 4px;">
                        ${e.hasUpdate?R`<span style="color: var(--unraid-warning);">${J(q,14)}</span>`:B}
                        ${e.restartEntityId?R`
                              <button
                                class="btn-icon"
                                style="padding: 2px;"
                                title="Restart ${e.name}"
                                @click=${t=>{t.stopPropagation(),this.pressButton(e.restartEntityId)}}
                              >
                                ${J(Ye,14)}
                              </button>
                            `:B}
                        <button
                          class="btn-icon"
                          style="padding: 2px; color: ${e.isRunning?`var(--unraid-online)`:`var(--unraid-subtext)`};"
                          title="${e.isRunning?`Stop`:`Start`} ${e.name}"
                          @click=${t=>{t.stopPropagation(),this.handleToggle(e.switchEntityId,e.isRunning,e.name)}}
                        >
                          ${J(Je,14)}
                        </button>
                      </div>
                    </div>
                  `)}
              </div>
            `:R`
              <div class="item-list">
                ${a.map(e=>R`
                    <div class="list-row">
                      <div class="row-left">
                        <span class="status-dot ${e.isRunning?`online`:`offline`}"></span>
                        <span style="font-weight: 600; min-width: 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                          ${e.name}
                        </span>
                        ${e.cpuPct===void 0?B:R`<span style="font-size: 0.72rem; color: var(--unraid-subtext);">${e.cpuPct}% CPU</span>`}
                        ${e.memoryUsage?R`<span style="font-size: 0.72rem; color: var(--unraid-subtext);">${e.memoryUsage}</span>`:B}
                      </div>
                      <div class="row-right">
                        ${e.hasUpdate?R`
                              <span class="badge badge-warning">Update Available</span>
                            `:B}
                        ${e.restartEntityId?R`
                              <button
                                class="btn"
                                style="padding: 3px 8px;"
                                @click=${()=>this.pressButton(e.restartEntityId)}
                              >
                                ${J(Ye,13)}
                                <span>Restart</span>
                              </button>
                            `:B}
                        <button
                          class="btn ${e.isRunning?`btn`:`btn-primary`}"
                          style="padding: 3px 8px;"
                          @click=${()=>this.handleToggle(e.switchEntityId,e.isRunning,e.name)}
                        >
                          ${J(Je,13)}
                          <span>${e.isRunning?`Stop`:`Start`}</span>
                        </button>
                      </div>
                    </div>
                  `)}
              </div>
            `}
      </ha-card>
    `}},editor:st,name:`Unraid Docker Containers Card`,description:`Monitor, start, stop, restart, and update Docker containers in grid or list view.`}),Z({tag:Ee,editorTag:De,card:class extends Y{static editorTag=De;render(){let e=this.getEntity(`ups_status`),t=this.getEntity(`ups_battery`),n=this.getEntity(`ups_load`),r=this.getEntity(`ups_runtime`),i=this.getEntity(`ups_power`),a=this.getEntity(`ups_output_voltage`),o=this.getEntity(`ups_battery_health`),s=!!(e&&e.state!==`unavailable`&&e.state!==`unknown`),c=s&&e?e.state:e?.state||`Unavailable`,l=s&&c.toLowerCase().includes(`online`),u=s&&(c.toLowerCase().includes(`battery`)||c.toLowerCase().includes(`discharge`)),d=!s||c===`Unavailable`||c===`unavailable`,f=t&&t.state!==`unavailable`&&t.state!==`unknown`&&t?Math.round(Number(t.state)||0):null,p=n&&n.state!==`unavailable`&&n.state!==`unknown`&&n?Math.round(Number(n.state)||0):null,m=i&&i.state!==`unavailable`&&i.state!==`unknown`&&i?`${i.state} W`:null,h=r&&r.state!==`unavailable`&&r.state!==`unknown`&&r?`${r.state} min`:null,g=a&&a.state!==`unavailable`&&a.state!==`unknown`&&a?`${a.state} V`:null,_=o&&o.state!==`unavailable`&&o.state!==`unknown`&&o?o.state:null,v=R`
      <span class="badge ${d?`badge-standby`:l?`badge-online`:u?`badge-warning`:`badge-error`}">
        ${d?B:R`<span class="pulse-dot"></span>`}
        <span>${d?`Unavailable`:c}</span>
      </span>
    `;return R`
      <ha-card>
        ${this.renderHeader(this.config.title||`UPS Power & Battery`,e?.attributes?.model||`Uninterruptible Power Supply`,Ve,v)}

        <!-- Ring Gauges -->
        <div class="rings-grid" style="grid-template-columns: repeat(2, 1fr);">
          <!-- Battery -->
          <div class="ring-card">
            <div
              class="ring-gauge"
              style="--pct: ${f??0}; --ring-color: ${f===null?`var(--unraid-border)`:f<20?`var(--unraid-error)`:f<50?`var(--unraid-warning)`:`var(--unraid-online)`}"
            >
              <span class="ring-content">${f===null?`—`:`${f}%`}</span>
            </div>
            <span class="ring-label">Battery Level</span>
            <span class="ring-subtext">${h?`${h} left`:f===null?`No Data`:`Healthy`}</span>
          </div>

          <!-- Load -->
          <div class="ring-card">
            <div
              class="ring-gauge"
              style="--pct: ${p??0}; --ring-color: ${p===null?`var(--unraid-border)`:p>80?`var(--unraid-error)`:p>50?`var(--unraid-warning)`:`var(--unraid-info)`}"
            >
              <span class="ring-content">${p===null?`—`:`${p}%`}</span>
            </div>
            <span class="ring-label">UPS Load</span>
            <span class="ring-subtext">${m||(p===null?`No Data`:`${p}% capacity`)}</span>
          </div>
        </div>

        <div class="divider"></div>

        <!-- Power & Electrical Specs -->
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">Runtime Remaining</span>
            <span class="detail-val">${h||`—`}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Power Consumption</span>
            <span class="detail-val">${m||`—`}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Output Voltage</span>
            <span class="detail-val">${g||`—`}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Battery Health</span>
            <span class="detail-val" style="${_?`color: var(--unraid-online);`:``}">${_||`—`}</span>
          </div>
        </div>
      </ha-card>
    `}},editor:ct,name:`Unraid Power & UPS Card`,description:`Monitor UPS battery level, power draw in Watts, load %, and estimated runtime.`});function mt(e){let t=e.split(`.`)[1]||``;return t.replace(/^.*?_vm_reboot_/,``).replace(/^vm_reboot_/,``).replace(/^.*?_virtual_machine_status_/,``).replace(/^virtual_machine_status_/,``).replace(/^.*?_virtual_machine_/,``).replace(/^virtual_machine_/,``).replace(/_status$/,``).replace(/_virtual_machine$/,``)||t}Z({tag:Oe,editorTag:ke,card:class extends Y{static editorTag=ke;handleToggle(e,t,n){(!t||confirm(`Are you sure you want to shut down virtual machine "${n}"?`))&&this.toggleEntity(e)}getVms(){let e=this.getEntities(`virtual_machine`,`switch`),t=this.getEntities(`virtual_machine_status`,`sensor`),n=this.getEntities(`vm_reboot`,`button`),r=[];for(let i of e){let e=mt(i.entity_id),a=i.attributes.friendly_name||e,o=i.state===`on`,s=t.find(t=>mt(t.entity_id)===e)?.state||(o?`running`:`shut off`),c=n.find(t=>mt(t.entity_id)===e);r.push({id:e,name:a,isRunning:o,status:s,switchEntityId:i.entity_id,rebootEntityId:c?.entity_id})}return r.sort((e,t)=>e.isRunning&&!t.isRunning?-1:!e.isRunning&&t.isRunning?1:e.name.localeCompare(t.name))}render(){let e=this.getVms(),t=e.filter(e=>e.isRunning).length,n=R`
      <span class="badge ${t>0?`badge-online`:`badge-standby`}">
        ${t} Running
      </span>
    `;return R`
      <ha-card>
        ${this.renderHeader(this.config.title||`Virtual Machines`,`${t} running of ${e.length} VMs`,Ge,n)}

        <div class="item-list">
          ${e.length>0?e.map(e=>R`
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
                      ${e.rebootEntityId?R`
                            <button
                              class="btn"
                              style="padding: 3px 8px;"
                              title="Reboot VM"
                              @click=${()=>this.pressButton(e.rebootEntityId)}
                            >
                              ${J(Ye,13)}
                              <span>Reboot</span>
                            </button>
                          `:B}
                      <button
                        class="btn ${e.isRunning?`btn`:`btn-primary`}"
                        style="padding: 3px 8px;"
                        @click=${()=>this.handleToggle(e.switchEntityId,e.isRunning,e.name)}
                      >
                        ${J(Je,13)}
                        <span>${e.isRunning?`Stop`:`Start`}</span>
                      </button>
                    </div>
                  </div>
                `):R`<div style="text-align: center; color: var(--unraid-subtext); font-size: 0.8rem; padding: 12px;">No virtual machines configured</div>`}
        </div>
      </ha-card>
    `}},editor:lt,name:`Unraid Virtual Machines Card`,description:`Monitor and manage Unraid virtual machines.`}),Z({tag:Pe,editorTag:Fe,card:class extends Y{static editorTag=Fe;static properties={...Y.properties,_activeTab:{state:!0}};constructor(){super(),this._activeTab=`overview`}render(){let e=this.getActiveDevice(),t=this.config.title||e?.name_by_user||e?.name||`Unraid Server`;return R`
      <ha-card style="gap: 12px;">
        <div class="header">
          <div class="header-main">
            <div class="header-icon">${J(Xe,22)}</div>
            <div class="header-titles">
              <span class="header-title">${t} Dashboard</span>
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
            ${J(Xe,14)} Overview
          </button>
          <button
            class="tab-btn ${this._activeTab===`storage`?`active`:``}"
            @click=${()=>this._activeTab=`storage`}
          >
            ${J(Ue,14)} Storage & Disks
          </button>
          <button
            class="tab-btn ${this._activeTab===`shares`?`active`:``}"
            @click=${()=>this._activeTab=`shares`}
          >
            ${J(He,14)} Shares
          </button>
          <button
            class="tab-btn ${this._activeTab===`network`?`active`:``}"
            @click=${()=>this._activeTab=`network`}
          >
            ${J(We,14)} Network
          </button>
          <button
            class="tab-btn ${this._activeTab===`docker`?`active`:``}"
            @click=${()=>this._activeTab=`docker`}
          >
            ${J(Re,14)} Docker
          </button>
          <button
            class="tab-btn ${this._activeTab===`ups`?`active`:``}"
            @click=${()=>this._activeTab=`ups`}
          >
            ${J(Ve,14)} UPS Power
          </button>
          <button
            class="tab-btn ${this._activeTab===`vms`?`active`:``}"
            @click=${()=>this._activeTab=`vms`}
          >
            ${J(Ge,14)} VMs
          </button>
        </div>

        <!-- Tab Contents -->
        <div>
          ${this._activeTab===`overview`?R`<unraid-server-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-server-card`,embedded:!0}}></unraid-server-card>`:B}
          ${this._activeTab===`storage`?R`<unraid-storage-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-storage-card`,embedded:!0}}></unraid-storage-card>`:B}
          ${this._activeTab===`shares`?R`<unraid-shares-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-shares-card`,embedded:!0}}></unraid-shares-card>`:B}
          ${this._activeTab===`network`?R`<unraid-network-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-network-card`,embedded:!0}}></unraid-network-card>`:B}
          ${this._activeTab===`docker`?R`<unraid-docker-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-docker-card`,embedded:!0}}></unraid-docker-card>`:B}
          ${this._activeTab===`ups`?R`<unraid-ups-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-ups-card`,embedded:!0}}></unraid-ups-card>`:B}
          ${this._activeTab===`vms`?R`<unraid-vm-card .hass=${this.hass} .config=${{...this.config,type:`custom:unraid-vm-card`,embedded:!0}}></unraid-vm-card>`:B}
        </div>
      </ha-card>
    `}},editor:ut,name:`Unraid Unified Dashboard Card`,description:`All-in-one Unraid master card with tabbed overview, storage, docker, UPS, and VM monitoring.`});