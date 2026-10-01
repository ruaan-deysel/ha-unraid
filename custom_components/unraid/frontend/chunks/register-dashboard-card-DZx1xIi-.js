var e=globalThis,t=e.ShadowRoot&&(e.ShadyCSS===void 0||e.ShadyCSS.nativeShadow)&&`adoptedStyleSheets`in Document.prototype&&`replace`in CSSStyleSheet.prototype,n=Symbol(),r=new WeakMap,i=class{constructor(e,t,r){if(this._$cssResult$=!0,r!==n)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o,n=this.t;if(t&&e===void 0){let t=n!==void 0&&n.length===1;t&&(e=r.get(n)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),t&&r.set(n,e))}return e}toString(){return this.cssText}},a=e=>new i(typeof e==`string`?e:e+``,void 0,n),o=(e,...t)=>new i(e.length===1?e[0]:t.reduce((t,n,r)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if(typeof e==`number`)return e;throw Error(`Value passed to 'css' function must be a 'css' function result: `+e+`. Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.`)})(n)+e[r+1],e[0]),e,n),s=(n,r)=>{if(t)n.adoptedStyleSheets=r.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let t of r){let r=document.createElement(`style`),i=e.litNonce;i!==void 0&&r.setAttribute(`nonce`,i),r.textContent=t.cssText,n.appendChild(r)}},c=t?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t=``;for(let n of e.cssRules)t+=n.cssText;return a(t)})(e):e,{is:l,defineProperty:u,getOwnPropertyDescriptor:d,getOwnPropertyNames:ee,getOwnPropertySymbols:te,getPrototypeOf:ne}=Object,f=globalThis,p=f.trustedTypes,re=p?p.emptyScript:``,ie=f.reactiveElementPolyfillSupport,m=(e,t)=>e,h={toAttribute(e,t){switch(t){case Boolean:e=e?re:null;break;case Object:case Array:e=e==null?e:JSON.stringify(e)}return e},fromAttribute(e,t){let n=e;switch(t){case Boolean:n=e!==null;break;case Number:n=e===null?null:Number(e);break;case Object:case Array:try{n=JSON.parse(e)}catch{n=null}}return n}},g=(e,t)=>!l(e,t),_={attribute:!0,type:String,converter:h,reflect:!1,useDefault:!1,hasChanged:g};Symbol.metadata??=Symbol(`metadata`),f.litPropertyMetadata??=new WeakMap;var v=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=_){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){let n=Symbol(),r=this.getPropertyDescriptor(e,n,t);r!==void 0&&u(this.prototype,e,r)}}static getPropertyDescriptor(e,t,n){let{get:r,set:i}=d(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:r,set(t){let a=r?.call(this);i?.call(this,t),this.requestUpdate(e,a,n)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??_}static _$Ei(){if(this.hasOwnProperty(m(`elementProperties`)))return;let e=ne(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(m(`finalized`)))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(m(`properties`))){let e=this.properties,t=[...ee(e),...te(e)];for(let n of t)this.createProperty(n,e[n])}let e=this[Symbol.metadata];if(e!==null){let t=litPropertyMetadata.get(e);if(t!==void 0)for(let[e,n]of t)this.elementProperties.set(e,n)}this._$Eh=new Map;for(let[e,t]of this.elementProperties){let n=this._$Eu(e,t);n!==void 0&&this._$Eh.set(n,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){let t=[];if(Array.isArray(e)){let n=new Set(e.flat(1/0).reverse());for(let e of n)t.unshift(c(e))}else e!==void 0&&t.push(c(e));return t}static _$Eu(e,t){let n=t.attribute;return!1===n?void 0:typeof n==`string`?n:typeof e==`string`?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){let e=new Map,t=this.constructor.elementProperties;for(let n of t.keys())this.hasOwnProperty(n)&&(e.set(n,this[n]),delete this[n]);e.size>0&&(this._$Ep=e)}createRenderRoot(){let e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return s(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,n){this._$AK(e,n)}_$ET(e,t){let n=this.constructor.elementProperties.get(e),r=this.constructor._$Eu(e,n);if(r!==void 0&&!0===n.reflect){let i=(n.converter?.toAttribute===void 0?h:n.converter).toAttribute(t,n.type);this._$Em=e,i==null?this.removeAttribute(r):this.setAttribute(r,i),this._$Em=null}}_$AK(e,t){let n=this.constructor,r=n._$Eh.get(e);if(r!==void 0&&this._$Em!==r){let e=n.getPropertyOptions(r),i=typeof e.converter==`function`?{fromAttribute:e.converter}:e.converter?.fromAttribute===void 0?h:e.converter;this._$Em=r;let a=i.fromAttribute(t,e.type);this[r]=a??this._$Ej?.get(r)??a,this._$Em=null}}requestUpdate(e,t,n,r=!1,i){if(e!==void 0){let a=this.constructor;if(!1===r&&(i=this[e]),n??=a.getPropertyOptions(e),!((n.hasChanged??g)(i,t)||n.useDefault&&n.reflect&&i===this._$Ej?.get(e)&&!this.hasAttribute(a._$Eu(e,n))))return;this.C(e,t,n)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:n,reflect:r,wrapped:i},a){n&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,a??t??this[e]),!0!==i||a!==void 0)||(this._$AL.has(e)||(this.hasUpdated||n||(t=void 0),this._$AL.set(e,t)),!0===r&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}let e=this.constructor.elementProperties;if(e.size>0)for(let[t,n]of e){let{wrapped:e}=n,r=this[t];!0!==e||this._$AL.has(t)||r===void 0||this.C(t,void 0,n,r)}}let e=!1,t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};v.elementStyles=[],v.shadowRootOptions={mode:`open`},v[m(`elementProperties`)]=new Map,v[m(`finalized`)]=new Map,ie?.({ReactiveElement:v}),(f.reactiveElementVersions??=[]).push(`2.1.2`);var y=globalThis,b=e=>e,x=y.trustedTypes,S=x?x.createPolicy(`lit-html`,{createHTML:e=>e}):void 0,C=`$lit$`,w=`lit$${Math.random().toFixed(9).slice(2)}$`,T=`?`+w,ae=`<${T}>`,E=document,D=()=>E.createComment(``),O=e=>e===null||typeof e!=`object`&&typeof e!=`function`,k=Array.isArray,oe=e=>k(e)||typeof e?.[Symbol.iterator]==`function`,A=`[
\f\r]`,j=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,M=/-->/g,N=/>/g,P=RegExp(`>|${A}(?:([^\\s"'>=/]+)(${A}*=${A}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,`g`),F=/'/g,I=/"/g,L=/^(?:script|style|textarea|title)$/i,R=(e=>(t,...n)=>({_$litType$:e,strings:t,values:n}))(1),z=Symbol.for(`lit-noChange`),B=Symbol.for(`lit-nothing`),V=new WeakMap,H=E.createTreeWalker(E,129);function U(e,t){if(!k(e)||!e.hasOwnProperty(`raw`))throw Error(`invalid template strings array`);return S===void 0?t:S.createHTML(t)}var se=(e,t)=>{let n=e.length-1,r=[],i,a=t===2?`<svg>`:t===3?`<math>`:``,o=j;for(let t=0;t<n;t++){let n=e[t],s,c,l=-1,u=0;for(;u<n.length&&(o.lastIndex=u,c=o.exec(n),c!==null);)u=o.lastIndex,o===j?c[1]===`!--`?o=M:c[1]===void 0?c[2]===void 0?c[3]!==void 0&&(o=P):(L.test(c[2])&&(i=RegExp(`</`+c[2],`g`)),o=P):o=N:o===P?c[0]===`>`?(o=i??j,l=-1):c[1]===void 0?l=-2:(l=o.lastIndex-c[2].length,s=c[1],o=c[3]===void 0?P:c[3]===`"`?I:F):o===I||o===F?o=P:o===M||o===N?o=j:(o=P,i=void 0);let d=o===P&&e[t+1].startsWith(`/>`)?` `:``;a+=o===j?n+ae:l>=0?(r.push(s),n.slice(0,l)+C+n.slice(l)+w+d):n+w+(l===-2?t:d)}return[U(e,a+(e[n]||`<?>`)+(t===2?`</svg>`:t===3?`</math>`:``)),r]},W=class e{constructor({strings:t,_$litType$:n},r){let i;this.parts=[];let a=0,o=0,s=t.length-1,c=this.parts,[l,u]=se(t,n);if(this.el=e.createElement(l,r),H.currentNode=this.el.content,n===2||n===3){let e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;(i=H.nextNode())!==null&&c.length<s;){if(i.nodeType===1){if(i.hasAttributes())for(let e of i.getAttributeNames())if(e.endsWith(C)){let t=u[o++],n=i.getAttribute(e).split(w),r=/([.?@])?(.*)/.exec(t);c.push({type:1,index:a,name:r[2],strings:n,ctor:r[1]===`.`?le:r[1]===`?`?ue:r[1]===`@`?de:q}),i.removeAttribute(e)}else e.startsWith(w)&&(c.push({type:6,index:a}),i.removeAttribute(e));if(L.test(i.tagName)){let e=i.textContent.split(w),t=e.length-1;if(t>0){i.textContent=x?x.emptyScript:``;for(let n=0;n<t;n++)i.append(e[n],D()),H.nextNode(),c.push({type:2,index:++a});i.append(e[t],D())}}}else if(i.nodeType===8){if(i.data===T)c.push({type:2,index:a});else{let e=-1;for(;(e=i.data.indexOf(w,e+1))!==-1;)c.push({type:7,index:a}),e+=w.length-1}}a++}}static createElement(e,t){let n=E.createElement(`template`);return n.innerHTML=e,n}};function G(e,t,n=e,r){if(t===z)return t;let i=r===void 0?n._$Cl:n._$Co?.[r],a=O(t)?void 0:t._$litDirective$;return i?.constructor!==a&&(i?._$AO?.(!1),a===void 0?i=void 0:(i=new a(e),i._$AT(e,n,r)),r===void 0?n._$Cl=i:(n._$Co??=[])[r]=i),i!==void 0&&(t=G(e,i._$AS(e,t.values),i,r)),t}var ce=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:t},parts:n}=this._$AD,r=(e?.creationScope??E).importNode(t,!0);H.currentNode=r;let i=H.nextNode(),a=0,o=0,s=n[0];for(;s!==void 0;){if(a===s.index){let t;s.type===2?t=new K(i,i.nextSibling,this,e):s.type===1?t=new s.ctor(i,s.name,s.strings,this,e):s.type===6&&(t=new fe(i,this,e)),this._$AV.push(t),s=n[++o]}a!==s?.index&&(i=H.nextNode(),a++)}return H.currentNode=E,r}p(e){let t=0;for(let n of this._$AV)n!==void 0&&(n.strings===void 0?n._$AI(e[t]):(n._$AI(e,n,t),t+=n.strings.length-2)),t++}},K=class e{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,n,r){this.type=2,this._$AH=B,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=n,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=G(this,e,t),O(e)?e===B||e==null||e===``?(this._$AH!==B&&this._$AR(),this._$AH=B):e!==this._$AH&&e!==z&&this._(e):e._$litType$===void 0?e.nodeType===void 0?oe(e)?this.k(e):this._(e):this.T(e):this.$(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==B&&O(this._$AH)?this._$AA.nextSibling.data=e:this.T(E.createTextNode(e)),this._$AH=e}$(e){let{values:t,_$litType$:n}=e,r=typeof n==`number`?this._$AC(e):(n.el===void 0&&(n.el=W.createElement(U(n.h,n.h[0]),this.options)),n);if(this._$AH?._$AD===r)this._$AH.p(t);else{let e=new ce(r,this),n=e.u(this.options);e.p(t),this.T(n),this._$AH=e}}_$AC(e){let t=V.get(e.strings);return t===void 0&&V.set(e.strings,t=new W(e)),t}k(t){k(this._$AH)||(this._$AH=[],this._$AR());let n=this._$AH,r,i=0;for(let a of t)i===n.length?n.push(r=new e(this.O(D()),this.O(D()),this,this.options)):r=n[i],r._$AI(a),i++;i<n.length&&(this._$AR(r&&r._$AB.nextSibling,i),n.length=i)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){let t=b(e).nextSibling;b(e).remove(),e=t}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},q=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,n,r,i){this.type=1,this._$AH=B,this._$AN=void 0,this.element=e,this.name=t,this._$AM=r,this.options=i,n.length>2||n[0]!==``||n[1]!==``?(this._$AH=Array(n.length-1).fill(new String),this.strings=n):this._$AH=B}_$AI(e,t=this,n,r){let i=this.strings,a=!1;if(i===void 0)e=G(this,e,t,0),a=!O(e)||e!==this._$AH&&e!==z,a&&(this._$AH=e);else{let r=e,o,s;for(e=i[0],o=0;o<i.length-1;o++)s=G(this,r[n+o],t,o),s===z&&(s=this._$AH[o]),a||=!O(s)||s!==this._$AH[o],s===B?e=B:e!==B&&(e+=(s??``)+i[o+1]),this._$AH[o]=s}a&&!r&&this.j(e)}j(e){e===B?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??``)}},le=class extends q{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===B?void 0:e}},ue=class extends q{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==B)}},de=class extends q{constructor(e,t,n,r,i){super(e,t,n,r,i),this.type=5}_$AI(e,t=this){if((e=G(this,e,t,0)??B)===z)return;let n=this._$AH,r=e===B&&n!==B||e.capture!==n.capture||e.once!==n.once||e.passive!==n.passive,i=e!==B&&(n===B||r);r&&this.element.removeEventListener(this.name,this,n),i&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH==`function`?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},fe=class{constructor(e,t,n){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=n}get _$AU(){return this._$AM._$AU}_$AI(e){G(this,e)}},pe=y.litHtmlPolyfillSupport;pe?.(W,K),(y.litHtmlVersions??=[]).push(`3.3.3`);var me=(e,t,n)=>{let r=n?.renderBefore??t,i=r._$litPart$;if(i===void 0){let e=n?.renderBefore??null;r._$litPart$=i=new K(t.insertBefore(D(),e),e,void 0,n??{})}return i._$AI(e),i},J=globalThis,Y=class extends v{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=me(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return z}};Y._$litElement$=!0,Y.finalized=!0,J.litElementHydrateSupport?.({LitElement:Y});var he=J.litElementPolyfillSupport;he?.({LitElement:Y}),(J.litElementVersions??=[]).push(`4.2.2`);var ge=`unraid-server-card`,_e=`unraid-server-card-editor`,ve=`unraid-storage-card`,ye=`unraid-storage-card-editor`,be=`unraid-docker-card`,xe=`unraid-docker-card-editor`,Se=`unraid-ups-card`,Ce=`unraid-ups-card-editor`,we=`unraid-vm-card`,Te=`unraid-vm-card-editor`,Ee=`unraid-dashboard-card`,De=`unraid-dashboard-card-editor`,Oe=[o`
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
  `];function X(e,t,n,r){let i=new CustomEvent(t,{bubbles:r?.bubbles??!0,cancelable:!!r?.cancelable,composed:r?.composed??!0,detail:n});return e.dispatchEvent(i),i}var ke=`M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z`,Ae=`M12 2C6.5 2 2 6.5 2 12S6.5 22 12 22 22 17.5 22 12 17.5 2 12 2M10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z`,je=`M21.81 10.25C21.75 10.21 21.25 9.82 20.17 9.82C19.89 9.82 19.61 9.85 19.33 9.9C19.12 8.5 17.95 7.79 17.9 7.76L17.61 7.59L17.43 7.86C17.19 8.22 17 8.63 16.92 9.05C16.72 9.85 16.84 10.61 17.25 11.26C16.76 11.54 15.96 11.61 15.79 11.61H2.62C2.28 11.61 2 11.89 2 12.24C2 13.39 2.18 14.54 2.58 15.62C3.03 16.81 3.71 17.69 4.58 18.23C5.56 18.83 7.17 19.17 9 19.17C9.79 19.17 10.61 19.1 11.42 18.95C12.54 18.75 13.62 18.36 14.61 17.79C15.43 17.32 16.16 16.72 16.78 16C17.83 14.83 18.45 13.5 18.9 12.35H19.09C20.23 12.35 20.94 11.89 21.33 11.5C21.59 11.26 21.78 10.97 21.92 10.63L22 10.39L21.81 10.25M3.85 11.24H5.61C5.69 11.24 5.77 11.17 5.77 11.08V9.5C5.77 9.42 5.7 9.34 5.61 9.34H3.85C3.76 9.34 3.69 9.41 3.69 9.5V11.08C3.7 11.17 3.76 11.24 3.85 11.24M6.28 11.24H8.04C8.12 11.24 8.2 11.17 8.2 11.08V9.5C8.2 9.42 8.13 9.34 8.04 9.34H6.28C6.19 9.34 6.12 9.41 6.12 9.5V11.08C6.13 11.17 6.19 11.24 6.28 11.24M8.75 11.24H10.5C10.6 11.24 10.67 11.17 10.67 11.08V9.5C10.67 9.42 10.61 9.34 10.5 9.34H8.75C8.67 9.34 8.6 9.41 8.6 9.5V11.08C8.6 11.17 8.66 11.24 8.75 11.24M11.19 11.24H12.96C13.04 11.24 13.11 11.17 13.11 11.08V9.5C13.11 9.42 13.05 9.34 12.96 9.34H11.19C11.11 9.34 11.04 9.41 11.04 9.5V11.08C11.04 11.17 11.11 11.24 11.19 11.24M6.28 9H8.04C8.12 9 8.2 8.91 8.2 8.82V7.25C8.2 7.16 8.13 7.09 8.04 7.09H6.28C6.19 7.09 6.12 7.15 6.12 7.25V8.82C6.13 8.91 6.19 9 6.28 9M8.75 9H10.5C10.6 9 10.67 8.91 10.67 8.82V7.25C10.67 7.16 10.61 7.09 10.5 7.09H8.75C8.67 7.09 8.6 7.15 8.6 7.25V8.82C8.6 8.91 8.66 9 8.75 9M11.19 9H12.96C13.04 9 13.11 8.91 13.11 8.82V7.25C13.11 7.16 13.04 7.09 12.96 7.09H11.19C11.11 7.09 11.04 7.15 11.04 7.25V8.82C11.04 8.91 11.11 9 11.19 9M11.19 6.72H12.96C13.04 6.72 13.11 6.65 13.11 6.56V5C13.11 4.9 13.04 4.83 12.96 4.83H11.19C11.11 4.83 11.04 4.89 11.04 5V6.56C11.04 6.64 11.11 6.72 11.19 6.72M13.65 11.24H15.41C15.5 11.24 15.57 11.17 15.57 11.08V9.5C15.57 9.42 15.5 9.34 15.41 9.34H13.65C13.57 9.34 13.5 9.41 13.5 9.5V11.08C13.5 11.17 13.57 11.24 13.65 11.24`,Me=`M7,2V13H10V22L17,10H13L17,2H7Z`,Ne=`M6,2H18A2,2 0 0,1 20,4V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V4A2,2 0 0,1 6,2M12,4A6,6 0 0,0 6,10C6,13.31 8.69,16 12.1,16L11.22,13.77C10.95,13.29 11.11,12.68 11.59,12.4L12.45,11.9C12.93,11.63 13.54,11.79 13.82,12.27L15.74,14.69C17.12,13.59 18,11.9 18,10A6,6 0 0,0 12,4M12,9A1,1 0 0,1 13,10A1,1 0 0,1 12,11A1,1 0 0,1 11,10A1,1 0 0,1 12,9M7,18A1,1 0 0,0 6,19A1,1 0 0,0 7,20A1,1 0 0,0 8,19A1,1 0 0,0 7,18M12.09,13.27L14.58,19.58L17.17,18.08L12.95,12.77L12.09,13.27Z`,Pe=`M21,16H3V4H21M21,2H3C1.89,2 1,2.89 1,4V16A2,2 0 0,0 3,18H10V20H8V22H16V20H14V18H21A2,2 0 0,0 23,16V4C23,2.89 22.1,2 21,2Z`,Fe=`M14,19H18V5H14M6,19H10V5H6V19Z`,Ie=`M8,5.14V19.14L19,12.14L8,5.14Z`,Le=`M16.56,5.44L15.11,6.89C16.84,7.94 18,9.83 18,12A6,6 0 0,1 12,18A6,6 0 0,1 6,12C6,9.83 7.16,7.94 8.88,6.88L7.44,5.44C5.36,6.88 4,9.28 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12C20,9.28 18.64,6.88 16.56,5.44M13,3H11V13H13`,Re=`M12,4C14.1,4 16.1,4.8 17.6,6.3C20.7,9.4 20.7,14.5 17.6,17.6C15.8,19.5 13.3,20.2 10.9,19.9L11.4,17.9C13.1,18.1 14.9,17.5 16.2,16.2C18.5,13.9 18.5,10.1 16.2,7.7C15.1,6.6 13.5,6 12,6V10.6L7,5.6L12,0.6V4M6.3,17.6C3.7,15 3.3,11 5.1,7.9L6.6,9.4C5.5,11.6 5.9,14.4 7.8,16.2C8.3,16.7 8.9,17.1 9.6,17.4L9,19.4C8,19 7.1,18.4 6.3,17.6Z`,ze=`M4,1H20A1,1 0 0,1 21,2V6A1,1 0 0,1 20,7H4A1,1 0 0,1 3,6V2A1,1 0 0,1 4,1M4,9H20A1,1 0 0,1 21,10V14A1,1 0 0,1 20,15H4A1,1 0 0,1 3,14V10A1,1 0 0,1 4,9M4,17H20A1,1 0 0,1 21,18V22A1,1 0 0,1 20,23H4A1,1 0 0,1 3,22V18A1,1 0 0,1 4,17M9,5H10V3H9V5M9,13H10V11H9V13M9,21H10V19H9V21M5,3V5H7V3H5M5,11V13H7V11H5M5,19V21H7V19H5Z`,Be=`M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5M11,7H13V13H11M11,15H13V17H11`,Ve=`M10,17L6,13L7.41,11.59L10,14.17L16.59,7.58L18,9M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1Z`,He=`M3,11H11V3H3M3,21H11V13H3M13,21H21V13H13M13,3V11H21V3`,Ue=`M9,5V9H21V5M9,19H21V15H9M9,14H21V10H9M4,9H8V5H4M4,19H8V15H4M4,14H8V10H4V14Z`;function Z(e,t=20,n=`icon`){return R`
    <svg
      class="${n}"
      style="width: ${t}px; height: ${t}px;"
      viewBox="0 0 24 24"
    >
      <path d="${e}" fill="currentColor"></path>
    </svg>
  `}var We=class extends Y{static styles=Oe;static editorTag=``;static async getConfigElement(){return document.createElement(this.editorTag)}static properties={hass:{attribute:!1},config:{attribute:!1}};constructor(){super(),this.config={type:``}}willUpdate(e){super.willUpdate(e),e.has(`config`)&&(this.config.embedded?this.setAttribute(`embedded`,``):this.removeAttribute(`embedded`))}setConfig(e){if(!e||typeof e.type!=`string`)throw Error(`Invalid card configuration`);this.config={...e},this.config.embedded?this.setAttribute(`embedded`,``):this.removeAttribute(`embedded`)}getCardSize(){return 4}getGridOptions(){return{columns:6,rows:4,min_columns:3,min_rows:3}}getUnraidDevices(){return this.hass?.devices?Object.values(this.hass.devices).filter(e=>e.identifiers?.some(([e])=>e===`unraid`)):[]}getActiveDevice(){let e=this.getUnraidDevices();if(e.length!==0){if(this.config.server){let t=e.find(e=>e.id===this.config.server||e.name?.toLowerCase()===this.config.server?.toLowerCase()||e.name_by_user?.toLowerCase()===this.config.server?.toLowerCase());if(t)return t}return e[0]}}getEntity(e,t){if(!this.hass?.states)return;let n=this.getActiveDevice(),r=n?.id;if(this.hass.entities&&r){for(let n of Object.values(this.hass.entities))if(n.device_id===r&&n.translation_key===e&&(!t||n.entity_id.startsWith(`${t}.`))){let e=this.hass.states[n.entity_id];if(e)return e}}return Object.values(this.hass.states).find(r=>{if(t&&!r.entity_id.startsWith(`${t}.`))return!1;if(this.hass?.entities){let e=this.hass.entities[r.entity_id];if(e&&e.platform!==`unraid`)return!1}let i=r.entity_id.split(`.`)[1]||``,a=i.endsWith(`_${e}`)||i===e;if(n?.name){let e=n.name.toLowerCase().replace(/[^a-z0-9]/g,`_`);return a&&i.includes(e)}return a})}getEntities(e,t){if(!this.hass?.states)return[];let n=this.getActiveDevice(),r=n?.id;if(this.hass.entities&&r){let n=[];for(let i of Object.values(this.hass.entities))if(i.device_id===r&&i.translation_key===e&&(!t||i.entity_id.startsWith(`${t}.`))){let e=this.hass.states[i.entity_id];e&&n.push(e)}if(n.length>0)return n}let i=n?.name?n.name.toLowerCase().replace(/[^a-z0-9]/g,`_`):void 0,a=t=>{if(this.hass?.entities){let e=this.hass.entities[t.entity_id];if(e&&e.platform!==`unraid`)return!1}if(e===`disk_usage`)return(t.entity_id.includes(`_disk_`)||t.entity_id.includes(`_cache`)||t.entity_id.includes(`_parity`)||t.entity_id.includes(`_boot`)||t.entity_id.includes(`_flash`))&&t.entity_id.endsWith(`_usage`)&&!t.entity_id.includes(`_array_usage`)&&!t.entity_id.includes(`_share_`);if(e===`disk_temperature`)return(t.entity_id.includes(`_disk_`)||t.entity_id.includes(`_cache`)||t.entity_id.includes(`_parity`)||t.entity_id.includes(`_boot`))&&(t.entity_id.endsWith(`_temperature`)||t.entity_id.includes(`_temp`));if(e===`disk_spin`)return(t.entity_id.includes(`_disk_`)||t.entity_id.includes(`_cache`)||t.entity_id.includes(`_parity`))&&t.entity_id.includes(`_spin`);let n=t.entity_id.split(`.`)[1]||``;return n===e||n.endsWith(`_${e}`)||n.includes(`_${e}_`)||n.startsWith(`${e}_`)},o=Object.values(this.hass.states),s=t?o.filter(e=>e.entity_id.startsWith(`${t}.`)):o;return i?s.filter(e=>e.entity_id.includes(i)&&a(e)):s.filter(e=>a(e))}findEntity(e){if(this.hass?.states)return typeof e==`string`?this.hass.states[e]:Object.values(this.hass.states).find(t=>e.test(t.entity_id))}async toggleEntity(e){if(!this.hass)return;let t=e.split(`.`)[0]||`homeassistant`;await this.hass.callService(t,`toggle`,{entity_id:e})}async pressButton(e){this.hass&&await this.hass.callService(`button`,`press`,{entity_id:e})}openMoreInfo(e){X(this,`hass-more-info`,{entityId:e})}renderHeader(e,t,n,r){return this.config.embedded||this.config.hide_header?B:R`
      <div class="header">
        <div class="header-main">
          <div class="header-icon">${Z(n,22)}</div>
          <div class="header-titles">
            <span class="header-title">${e}</span>
            <span class="header-subtitle">${t}</span>
          </div>
        </div>
        ${r?R`<div class="header-actions">${r}</div>`:``}
      </div>
    `}},Q=class extends Y{static properties={hass:{attribute:!1},_config:{state:!0}};static styles=o`
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
  `;setConfig(e){this._config={...e}}_valueChanged(e,t){this._config&&(this._config={...this._config,[e]:t},X(this,`config-changed`,{config:this._config}))}render(){if(!this._config)return R``;let e=this.hass?.devices?Object.values(this.hass.devices).filter(e=>e.identifiers?.some(([e])=>e===`unraid`)):[];return R`
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
    `}},Ge=class extends Q{},Ke=class extends Q{},qe=class extends Q{},Je=class extends Q{},Ye=class extends Q{},Xe=class extends Q{};function $(e,t){if(!customElements.get(e))try{customElements.define(e,t)}catch(n){if(n instanceof Error&&(n.name===`NotSupportedError`||n.message.includes(`already been registered`))){class n extends t{}customElements.define(e,n)}else throw n}}function Ze(e){$(e.tag,e.card),$(e.editorTag,e.editor),window.customCards??=[],window.customCards.some(t=>t.type===e.tag)||window.customCards.push({type:e.tag,name:e.name,description:e.description,preview:!0,documentationURL:`https://github.com/ruaan-deysel/ha-unraid`})}export{_e as A,He as C,be as D,De as E,we as F,Te as I,B as L,ye as M,Se as N,xe as O,Ce as P,R,Ve as S,Ee as T,Ie as _,Ke as a,ze as b,We as c,Ae as d,je as f,Fe as g,Pe as h,Ge as i,ve as j,ge as k,Z as l,Ne as m,Xe as n,Je as o,Me as p,qe as r,Ye as s,Ze as t,ke as u,Le as v,Ue as w,Be as x,Re as y};
