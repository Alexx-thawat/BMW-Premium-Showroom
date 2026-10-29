
/* ===== app.js ===== */
const state={user:null,name:'',cars:[],visitor:sessionStorage.getItem('bmwVisitor')==='1',role:'customer',selectedColor:null};
const app=document.querySelector('#app'),nav=document.querySelector('#nav'),account=document.querySelector('#account');
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const baht=v=>new Intl.NumberFormat('th-TH',{style:'currency',currency:'THB',minimumFractionDigits:0}).format(Number(v||0));
const statusLabel={AwaitingPayment:'รอชำระค่าจอง',PaymentReview:'รอตรวจสลิป',Booked:'ยืนยันจองแล้ว',Completed:'ซื้อสำเร็จ',CancelRequested:'รออนุมัติยกเลิก',Cancelled:'ยกเลิกแล้ว',Unavailable:'รถไม่พร้อมขาย',Available:'พร้อมขาย',Reserved:'ถูกจองไว้',Sold:'ขายแล้ว'};
async function api(path,opt={}){const res=await fetch(path,{headers:{'Content-Type':'application/json',...(opt.headers||{})},...opt});const out=await res.json().catch(()=>({error:'ระบบตอบกลับไม่ถูกต้อง'}));if(!res.ok)throw Error(out.error||'ทำรายการไม่สำเร็จ');return out}
function toast(msg,error=false){const el=document.querySelector('#toast');el.textContent=msg;el.className=error?'show error':'show';setTimeout(()=>el.className='',3200)}
function modal(html){document.querySelector('#modalBody').innerHTML=html;document.querySelector('#modal').classList.remove('hidden')}
function closeModal(){document.querySelector('#modal').classList.add('hidden')}
window.closeModal=closeModal;
function setNav(items,active){nav.innerHTML=items.map(([key,label])=>`<button class="${key===active?'active':''}" onclick="location.hash='${key}'">${label}</button>`).join('')}
function menuFor(role){if(role==='customer')return [['customer','สรุปของฉัน'],['catalog','เลือกรถ'],['orders','การจอง / สั่งซื้อ'],['profile','ข้อมูลของฉัน']];if(role==='employee')return [['bookings','จอง / ชำระเงิน'],['inventory','รถยนต์'],['customers','ข้อมูลลูกค้า'],['visitors','ผู้เข้าชม'],['sales','รายการขาย']];if(role==='executive')return [['executive','แดชบอร์ดผู้บริหาร'],['exec-inventory','ภาพรวมรถ'],['exec-sales','ยอดขาย'],['exec-employees','พนักงาน']];return [['catalog','เลือกรถ']]}
async function refreshSession(){const s=await api('/api/session');if(s.version!=='2026.10.27-stock-v2'&&location.port!=='8772'){location.replace('http://127.0.0.1:8772'+location.pathname+location.hash);return;}state.user=s.user;state.name=s.name;account.textContent=state.user?`${state.name} • ${{customer:'ลูกค้า',employee:'พนักงาน',executive:'CEO / ผู้บริหาร'}[state.user.role]} ▾`:'เข้าสู่ระบบ';account.onclick=state.user?logout:()=>location.hash='login'}
async function logout(){await api('/api/logout',{method:'POST',body:'{}'});state.user=null;state.name='';toast('ออกจากระบบแล้ว');location.hash='catalog';await route()}
function hero(){return `<section class="hero hero-clean"><div class="hero-copy"><div class="eyebrow">Sheer Driving Pleasure</div><h1>ค้นพบ BMW<br>ที่ใช่สำหรับคุณ</h1><p>สัมผัสรถยนต์ระดับพรีเมียม</p><button class="btn" onclick="document.querySelector('#catalog').scrollIntoView()">สำรวจรถทั้งหมด</button></div></section>`}
async function visitorGate(){setNav([],null);app.innerHTML=`<section class="auth"><form class="auth-card" id="visitorForm"><div class="eyebrow">WELCOME TO BMW</div><h1>ก่อนเข้าชมรถ</h1><p>กรอกชื่อและเบอร์โทรเพื่อรับชมแคตตาล็อก ยังไม่ใช่การสมัครสมาชิก</p><div class="field"><label>ชื่อผู้เข้าชม</label><input name="name" required minlength="2" placeholder="ชื่อ–นามสกุล"></div><div class="field"><label>เบอร์โทรศัพท์</label><input name="phone" required pattern="0[0-9]{8,9}" placeholder="0XXXXXXXXX"></div><button class="btn full">เข้าสู่โชว์รูม</button></form></section>`;document.querySelector('#visitorForm').onsubmit=async e=>{e.preventDefault();const d=Object.fromEntries(new FormData(e.target));try{await api('/api/visitor',{method:'POST',body:JSON.stringify(d)});sessionStorage.setItem('bmwVisitor','1');state.visitor=true;route()}catch(x){toast(x.message,true)}}}
async function loadCars(){state.cars=await api('/api/cars')}
async function catalog(){if(!state.visitor&&!state.user)return visitorGate();await loadCars();setNav(state.user?menuFor(state.user.role):[['catalog','เลือกรถ']],'catalog');const series=[...new Set(state.cars.map(c=>c.series))];app.innerHTML=hero()+`<section class="section" id="catalog"><div class="section-head"><div><h2>BMW รุ่นที่พร้อมขาย</h2><p>จำนวนและสีคำนวณจากฐานข้อมูลปัจจุบัน</p></div><strong>${state.cars.length} รุ่น</strong></div><div class="toolbar"><input id="search" placeholder="ค้นหารุ่นรถหรือซีรีส์"></div><div class="catalog-layout"><aside class="filters"><button class="on" data-series="">รถทั้งหมด</button><h3>Series</h3>${series.map(x=>`<button data-series="${esc(x)}">${esc(x)}</button>`).join('')}</aside><div class="grid" id="carGrid"></div></div></section>`;const draw=(q='',s='')=>{const rows=state.cars.filter(c=>(c.model+' '+c.series).toLowerCase().includes(q.toLowerCase())&&(!s||c.series===s));document.querySelector('#carGrid').innerHTML=rows.map(c=>`<article class="car-card"><img loading="lazy" src="/api/car-image?id=${c.car_id}&slot=1"><div class="car-body"><div class="series">BMW • ${esc(c.series)}</div><h3>${esc(c.model)}</h3><div>${c.year} • ${c.colors.reduce((a,x)=>a+Number(x.quantity),0)} คันพร้อมขาย</div><div class="price">${baht(c.price)}</div><div class="card-actions"><button class="btn dark" onclick="openCar(${c.car_id})">ดูรายละเอียด</button>${state.user?.role==='customer'?`<button class="btn" onclick="openCar(${c.car_id},true)">เลือกซื้อ</button>`:''}</div></div></article>`).join('')||'<div class="empty">ไม่พบรถที่ค้นหา</div>'};draw();document.querySelector('#search').oninput=e=>draw(e.target.value,document.querySelector('.filters .on').dataset.series);document.querySelectorAll('.filters button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.filters button').forEach(x=>x.classList.remove('on'));b.classList.add('on');draw(document.querySelector('#search').value,b.dataset.series)})}
async function openCar(id,buy=false){const c=await api('/api/car?id='+id);setNav(state.user?menuFor(state.user.role):[['catalog','เลือกรถ']],'catalog');app.innerHTML=`<section class="section"><button class="btn ghost" onclick="location.hash='catalog'">← กลับไปดูรถ</button><div class="detail"><div><img id="mainPhoto" class="gallery-main" src="/api/car-image?id=${c.car_id}&slot=1"><div class="thumbs">${[1,2,3].map(n=>`<img src="/api/car-image?id=${c.car_id}&slot=${n}" onerror="this.style.display='none'" onclick="mainPhoto.src=this.src">`).join('')}</div></div><div><div class="eyebrow">${esc(c.series)}</div><h1>${esc(c.model)}</h1><p>${c.year} • ${esc(c.color)}</p><div class="price">${baht(c.price)}</div><h3>สีที่พร้อมขาย</h3><div class="colors">${c.colors.map((x,i)=>`<button class="color-choice ${i===0?'on':''}" data-id="${x.car_id}" onclick="chooseColor(this)">${esc(x.color)} • เหลือ ${x.quantity} คัน</button>`).join('')}</div><p>${esc(c.description||'รายละเอียดรถยนต์ BMW ที่คัดสรรสำหรับคุณ')}</p>${state.user?.role==='customer'?'<button class="btn full" onclick="bookSelected()">เลือกซื้อ / จองรถคันนี้</button>':'<button class="btn full" onclick="location.hash=\'login\'">เข้าสู่ระบบก่อนสั่งซื้อ</button>'}</div></div></section>`;state.selectedColor=Number(c.colors[0]?.car_id);if(buy&&state.user?.role==='customer')setTimeout(bookSelected,0)}
window.openCar=openCar;window.chooseColor=el=>{document.querySelectorAll('.color-choice').forEach(x=>x.classList.remove('on'));el.classList.add('on');state.selectedColor=Number(el.dataset.id)};
function bookSelected(){if(!state.selectedColor)return toast('ไม่มีสีที่พร้อมขาย',true);modal(`<h2>ยืนยันข้อมูลการจอง</h2><p>ระบบจะกันรถจากสต็อกทันที และชำระค่าจองแบบสาธิต 10,000 บาทภายหลัง</p><form id="bookForm" class="form-grid"><div class="field"><label>รูปแบบการซื้อ</label><select name="purchase_method"><option value="cash">ซื้อเงินสด</option><option value="finance">ขอสินเชื่อ</option></select></div><div class="field"><label>วันที่คาดว่าจะรับรถ</label><input type="date" name="delivery_date"></div><label class="wide"><input style="width:auto" type="checkbox" name="terms" required> ยอมรับเงื่อนไขการจองและการตรวจหลักฐานแบบสาธิต</label><button class="btn green wide">ยืนยันจองรถ</button></form>`);document.querySelector('#bookForm').onsubmit=async e=>{e.preventDefault();const d=Object.fromEntries(new FormData(e.target));d.car_id=state.selectedColor;d.terms_accepted=!!d.terms;try{const out=await api('/api/bookings',{method:'POST',body:JSON.stringify(d)});closeModal();toast('จองสำเร็จ เลขที่ '+out.request_id);location.hash='orders';route()}catch(x){toast(x.message,true)}}}
window.bookSelected=bookSelected;
async function login(){setNav([],null);app.innerHTML=`<section class="auth"><form class="auth-card" id="loginForm"><div class="eyebrow">BMW ACCOUNT</div><h1>เข้าสู่ระบบ</h1><p>เลือกประเภทบัญชีให้ตรงกับผู้ใช้งาน</p><div class="role-switch"><button type="button" class="on" data-role="customer">ลูกค้า</button><button type="button" data-role="employee">พนักงาน</button><button type="button" data-role="executive">CEO / ผู้บริหาร</button></div><div class="field"><label>ชื่อผู้ใช้</label><input name="username" required></div><div class="field"><label>รหัสผ่าน</label><input type="password" name="password" required></div><button class="btn full">เข้าสู่ระบบ</button><button type="button" class="btn ghost full" style="margin-top:8px" onclick="register()">ลงทะเบียนลูกค้าใหม่</button><button type="button" class="btn ghost full" style="margin-top:8px" onclick="resetForm()">ลืมรหัสผ่าน</button></form></section>`;document.querySelectorAll('.role-switch button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.role-switch button').forEach(x=>x.classList.remove('on'));b.classList.add('on');state.role=b.dataset.role});document.querySelector('#loginForm').onsubmit=async e=>{e.preventDefault();const d=Object.fromEntries(new FormData(e.target));d.role=state.role;try{await api('/api/login',{method:'POST',body:JSON.stringify(d)});await refreshSession();location.hash=state.user.role==='executive'?'executive':state.user.role==='employee'?'bookings':'customer';route()}catch(x){toast(x.message,true)}}}
function register(){modal(`<h2>ลงทะเบียนลูกค้า</h2><form id="registerForm" class="form-grid"><div class="field"><label>ชื่อ</label><input name="fname" required></div><div class="field"><label>นามสกุล</label><input name="lname" required></div><div class="field"><label>ชื่อผู้ใช้</label><input name="username" required></div><div class="field"><label>รหัสผ่านอย่างน้อย 8 ตัว</label><input type="password" name="password" minlength="8" required></div><div class="field"><label>เบอร์โทร</label><input name="phone" required></div><div class="field"><label>อีเมล</label><input type="email" name="email" required></div><div class="field wide"><label>ที่อยู่</label><textarea name="address" required></textarea></div><button class="btn wide">สร้างบัญชีลูกค้า</button></form>`);document.querySelector('#registerForm').onsubmit=async e=>{e.preventDefault();try{await api('/api/register',{method:'POST',body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});closeModal();toast('ลงทะเบียนสำเร็จ กรุณาเข้าสู่ระบบ')}catch(x){toast(x.message,true)}}}window.register=register;
function resetForm(){modal(`<h2>ตั้งรหัสผ่านใหม่</h2><p>ยืนยันด้วยเบอร์โทรและอีเมลที่บันทึกไว้</p><form id="resetForm" class="form-grid"><div class="field"><label>ประเภทบัญชี</label><select name="role"><option value="customer">ลูกค้า</option><option value="employee">พนักงาน</option><option value="executive">CEO / ผู้บริหาร</option></select></div><div class="field"><label>ชื่อผู้ใช้</label><input name="username" required></div><div class="field"><label>เบอร์โทร</label><input name="phone" required></div><div class="field"><label>อีเมล</label><input type="email" name="email" required></div><div class="field wide"><label>รหัสผ่านใหม่อย่างน้อย 8 ตัว</label><input type="password" name="password" minlength="8" required></div><button class="btn wide">ตั้งรหัสผ่านใหม่</button></form>`);document.querySelector('#resetForm').onsubmit=async e=>{e.preventDefault();try{await api('/api/reset-password',{method:'POST',body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});closeModal();toast('ตั้งรหัสผ่านใหม่แล้ว')}catch(x){toast(x.message,true)}}}
window.resetForm=resetForm;
function badge(s){const cls=['Completed','Booked'].includes(s)?'green':['Cancelled','Unavailable'].includes(s)?'red':['AwaitingPayment','PaymentReview','CancelRequested'].includes(s)?'gold':'';return `<span class="badge ${cls}">${esc(statusLabel[s]||s)}</span>`}
async function customer(){if(state.user?.role!=='customer')return login();setNav([['customer','สรุปของฉัน'],['catalog','เลือกรถ'],['orders','การจอง / สั่งซื้อ'],['profile','ข้อมูลของฉัน']],'customer');const d=await api('/api/customer/overview');const s=d.summary;app.innerHTML=`<section class="section"><div class="section-head"><div><h2>สวัสดี ${esc(state.name)}</h2><p>ภาพรวมการซื้อและการชำระเงินของคุณ</p></div><button class="btn" onclick="location.hash='catalog'">เลือกรถเพิ่ม</button></div><div class="stats"><div class="stat"><small>ซื้อสำเร็จ</small><strong>${s.bought_count} คัน</strong></div><div class="stat"><small>มูลค่ารถทั้งหมด</small><strong>${baht(s.order_total)}</strong></div><div class="stat"><small>ชำระแล้ว</small><strong>${s.paid_count} รายการ</strong></div><div class="stat"><small>ยังไม่ชำระครบ</small><strong>${s.unpaid_count} รายการ</strong></div></div>${bookingTable(d.bookings,true)}</section>`}
function bookingActions(r,customerView){if(customerView){let out='';if(r.status==='AwaitingPayment')out+=`<button class="btn" onclick='paymentForm(${JSON.stringify({id:r.request_id,amount:r.deposit_amount,purpose:"Deposit"})})'>ส่งค่าจอง</button>`;if(r.status==='Booked'&&Number(r.remaining_amount)>0)out+=`<button class="btn green" onclick='paymentForm(${JSON.stringify({id:r.request_id,amount:r.remaining_amount,purpose:"Balance"})})'>ชำระยอดคงเหลือ</button>`;if(['AwaitingPayment','PaymentReview','Booked'].includes(r.status))out+=` <button class="btn red" onclick="cancelBooking(${r.request_id},false)">ขอยกเลิก</button>`;return out||'-'}let out='';if(r.status==='Booked'&&Number(r.remaining_amount)===0)out+=`<button class="btn green" onclick="confirmSale(${r.request_id})">ยืนยันขาย</button>`;if(r.status==='CancelRequested')out+=`<button class="btn red" onclick="cancelBooking(${r.request_id},true)">อนุมัติยกเลิก</button>`;return out||'-'}
function bookingTable(rows,customerView=false){return `<div class="panel"><h3>${customerView?'รายการล่าสุด':'รายการจองและชำระเงิน'}</h3><div class="table-wrap"><table><thead><tr><th>เลขที่</th><th>ลูกค้า</th><th>รุ่น / สี</th><th>ชำระแล้ว</th><th>คงเหลือ</th><th>สถานะ</th><th>จัดการ</th></tr></thead><tbody>${rows.map(r=>`<tr><td>#${r.request_id}</td><td>${esc(r.customer)}</td><td>${esc(r.model)}<br><small>${esc(r.color)}</small></td><td>${baht(r.paid_amount)}</td><td>${baht(r.remaining_amount)}</td><td>${badge(r.status)}</td><td class="actions">${bookingActions(r,customerView)}</td></tr>`).join('')||'<tr><td colspan="7" class="empty">ยังไม่มีรายการ</td></tr>'}</tbody></table></div></div>`}
async function cancelBooking(id,approve){if(!confirm(approve?'อนุมัติยกเลิกรายการนี้หรือไม่?':'ส่งคำขอยกเลิกรายการนี้หรือไม่?'))return;try{await api('/api/bookings/cancel',{method:'POST',body:JSON.stringify({request_id:id,approve})});toast(approve?'อนุมัติยกเลิกแล้ว':'ส่งคำขอยกเลิกแล้ว');state.user.role==='employee'?bookings():orders()}catch(x){toast(x.message,true)}}
async function confirmSale(id){if(!confirm('ยืนยันว่าชำระครบและส่งมอบเพื่อบันทึกการขายหรือไม่?'))return;try{await api('/api/sales/confirm',{method:'POST',body:JSON.stringify({request_id:id})});toast('ยืนยันขายสำเร็จ');bookings()}catch(x){toast(x.message,true)}}
window.cancelBooking=cancelBooking;window.confirmSale=confirmSale;async function orders(){if(state.user?.role!=='customer')return login();setNav([['customer','สรุปของฉัน'],['catalog','เลือกรถ'],['orders','การจอง / สั่งซื้อ'],['profile','ข้อมูลของฉัน']],'orders');const d=await api('/api/customer/overview');app.innerHTML=`<section class="section"><div class="section-head"><div><h2>การจองของฉัน</h2><p>ติดตามการตรวจค่าจองและยอดคงเหลือ</p></div></div>${bookingTable(d.bookings,true)}</section>`}
function paymentForm(x){modal(`<h2>ส่งหลักฐานการชำระเงิน</h2><p>โหมดสาธิต ไม่มีการโอนเงินจริง • จำนวน ${baht(x.amount)}</p><form id="payForm"><div class="field"><label>วันเวลาที่ชำระ</label><input type="datetime-local" name="time" required></div><div class="field"><label>เลขอ้างอิง</label><input name="reference" required></div><div class="field"><label>ภาพสลิป JPG / PNG / WEBP</label><input type="file" name="slip" accept="image/*" required></div><button class="btn green full">ส่งให้พนักงานตรวจ</button></form>`);document.querySelector('#payForm').onsubmit=async e=>{e.preventDefault();const f=e.target.slip.files[0];const reader=new FileReader();reader.onload=async()=>{try{await api('/api/payments',{method:'POST',body:JSON.stringify({request_id:x.id,purpose:x.purpose,amount:x.amount,slip:reader.result,slip_name:f.name,transferred_at:e.target.time.value.replace('T',' ')+':00',reference:e.target.reference.value})});closeModal();toast('ส่งหลักฐานให้พนักงานแล้ว');orders()}catch(err){toast(err.message,true)}};reader.readAsDataURL(f)}}window.paymentForm=paymentForm;
function salesLine(items){const w=720,h=260,p=42,max=Math.max(...items.map(x=>Number(x.revenue)),1),step=(w-p*2)/Math.max(items.length-1,1);const pts=items.map((x,i)=>[p+i*step,h-p-(Number(x.revenue)/max)*(h-p*2)]);const line=pts.map((v,i)=>(i?'L':'M')+v[0].toFixed(1)+' '+v[1].toFixed(1)).join(' ');const area=`${line} L ${pts.at(-1)[0]} ${h-p} L ${pts[0][0]} ${h-p} Z`;return `<svg class="line-chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="กราฟยอดขายหกเดือน">${[0,.25,.5,.75,1].map(n=>`<line x1="${p}" y1="${h-p-n*(h-p*2)}" x2="${w-p}" y2="${h-p-n*(h-p*2)}" class="grid-line"/>`).join('')}<path d="${area}" class="chart-area"/><path d="${line}" class="chart-line"/>${pts.map((v,i)=>`<g><circle cx="${v[0]}" cy="${v[1]}" r="5"/><text x="${v[0]}" y="${h-13}" text-anchor="middle">${items[i].month.slice(5)}/${items[i].month.slice(2,4)}</text><title>${items[i].month}: ${baht(items[i].revenue)}</title></g>`).join('')}</svg>`}
function rankingBars(items){const rows=items.slice(0,6),max=Math.max(...rows.map(x=>Number(x.sold_count)),1);return rows.length?`<div class="rank-bars">${rows.map((x,i)=>`<div class="rank-row"><b>${i+1}</b><span title="${esc(x.model)}">${esc(x.model)}</span><div class="bar-track"><i style="width:${Math.max(8,Number(x.sold_count)/max*100)}%"></i></div><strong>${x.sold_count} คัน</strong><small>พร้อมขาย ${x.available_qty}</small></div>`).join('')}</div>`:'<div class="empty">ยังไม่มียอดขายสำเร็จในช่วงนี้</div>'}
function stockDonut(items){const total=items.reduce((a,x)=>a+Number(x.quantity),0)||1,available=Number(items.find(x=>x.status==='Available')?.quantity||0),reserved=Number(items.find(x=>x.status==='Reserved')?.quantity||0),a=available/total*100,b=(available+reserved)/total*100;return `<div class="stock-visual"><div class="donut" style="--a:${a}%;--b:${b}%"><div><strong>${total}</strong><small>คันทั้งหมด</small></div></div><div class="legend">${items.map((x,i)=>`<p><i class="dot d${i}"></i><span>${esc(statusLabel[x.status]||x.status)}</span><b>${x.quantity} คัน</b></p>`).join('')}</div></div>`}
function executiveDate(){return new Intl.DateTimeFormat('th-TH',{dateStyle:'long',timeStyle:'short'}).format(new Date())}
function growthText(current,previous){current=Number(current||0);previous=Number(previous||0);if(!previous)return current?'เริ่มมียอดขายในเดือนนี้':'ยังไม่มีฐานเปรียบเทียบ';const value=(current-previous)/previous*100;return `${value>=0?'▲':'▼'} ${Math.abs(value).toFixed(1)}% จากเดือนก่อน`}
async function executiveDashboard(period='all'){if(state.user?.role!=='executive')return login();setNav(menuFor('executive'),'executive');const d=await api('/api/executive/dashboard?period='+period),s=d.summary,best=d.ranking[0],current=d.monthly.at(-1)||{},previous=d.monthly.at(-2)||{},avg=s.sold_count?Number(s.revenue)/Number(s.sold_count):0,priority=d.recommendations.filter(x=>x.level==='สูง').length,stockTotal=d.stock_mix.reduce((a,x)=>a+Number(x.quantity),0),topShare=best&&s.sold_count?best.sold_count/s.sold_count*100:0;app.innerHTML=`<section class="section executive-dashboard"><div class="exec-masthead"><div><div class="exec-kicker"><span>BMW</span><i></i> EXECUTIVE INTELLIGENCE</div><h1>ภาพรวมธุรกิจ</h1><p>ข้อมูลยอดขาย สต็อก และงานที่ต้องติดตามสำหรับการตัดสินใจของผู้บริหาร</p></div><div class="exec-asof"><span><i></i> LIVE DATABASE</span><small>อัปเดตล่าสุด</small><strong>${executiveDate()}</strong></div></div><div class="exec-toolbar"><div class="period-tabs"><button class="${period==='all'?'on':''}" onclick="executivePeriod('all')">ทั้งหมด</button><button class="${period==='month'?'on':''}" onclick="executivePeriod('month')">เดือนนี้</button><button class="${period==='year'?'on':''}" onclick="executivePeriod('year')">ปีนี้</button></div><div class="data-note">นับเฉพาะรายการขายที่ยืนยันสำเร็จ</div></div><div class="exec-kpis"><article class="exec-kpi primary"><span>ยอดขายรวม</span><strong>${baht(s.revenue)}</strong><small>${growthText(current.revenue,previous.revenue)}</small></article><article class="exec-kpi"><span>ส่งมอบสำเร็จ</span><strong>${s.sold_count} <small>คัน</small></strong><small>ตามช่วงข้อมูลที่เลือก</small></article><article class="exec-kpi"><span>มูลค่าเฉลี่ยต่อคัน</span><strong>${baht(avg)}</strong><small>จากรายการขายสำเร็จ</small></article><article class="exec-kpi"><span>รถพร้อมขาย</span><strong>${s.available_qty} <small>คัน</small></strong><small>จากรถทั้งหมด ${stockTotal} คัน</small></article><article class="exec-kpi attention"><span>รายการต้องติดตาม</span><strong>${s.pending_slip_count} <small>รายการ</small></strong><small>หลักฐานชำระเงินรอตรวจ</small></article></div><div class="exec-brief"><article class="leader-card"><div class="leader-rank">01</div><div><span>MARKET LEADER</span><h2>${best?esc(best.model):'ยังไม่มีข้อมูลยอดขาย'}</h2><p>${best?`ครองสัดส่วน ${topShare.toFixed(1)}% ของรถที่ขายสำเร็จ • พร้อมขาย ${best.available_qty} คัน`:'เมื่อมีการยืนยันขาย ระบบจะจัดอันดับให้อัตโนมัติ'}</p></div><div class="leader-result"><small>ขายสำเร็จ</small><strong>${best?best.sold_count:0}</strong><span>คัน</span></div></article><article class="attention-card ${priority?'urgent':''}"><span>STOCK ATTENTION</span><strong>${priority}</strong><h3>รุ่นที่ควรตรวจแผนเติมรถ</h3><p>${priority?'ยอดขายเทียบสต็อกอยู่ในระดับที่ควรพิจารณา':'ยังไม่มีรุ่นที่ต้องเร่งตรวจสต็อก'}</p></article></div><div class="chart-grid executive-charts"><article class="chart-card wide-chart"><header><div><span class="chart-code">01 / SALES TREND</span><h3>แนวโน้มมูลค่ายอดขาย</h3><p>เปรียบเทียบรายการขายสำเร็จย้อนหลัง 6 เดือน</p></div><div class="chart-highlight"><small>เดือนล่าสุด</small><strong>${baht(current.revenue||0)}</strong></div></header>${salesLine(d.monthly)}</article><article class="chart-card"><header><div><span class="chart-code">02 / INVENTORY</span><h3>โครงสร้างสต็อก</h3><p>สถานะรถทั้งหมดในระบบ</p></div></header>${stockDonut(d.stock_mix)}</article><article class="chart-card wide-chart"><header><div><span class="chart-code">03 / MODEL RANKING</span><h3>อันดับรถขายดี</h3><p>ยอดขายสำเร็จเทียบรถพร้อมขาย</p></div></header>${rankingBars(d.ranking)}</article><article class="chart-card"><header><div><span class="chart-code">04 / ACTION LIST</span><h3>รายการเพื่อการตัดสินใจ</h3><p>เรียงตามระดับความสำคัญของสต็อก</p></div></header><div class="recommend-list">${d.recommendations.slice(0,6).map(r=>`<div class="recommend ${r.level==='สูง'?'high':r.level==='เฝ้าระวัง'?'watch':'normal'}"><div><b>${esc(r.model)}</b><span>ขาย ${r.sold_count} • พร้อมขาย ${r.available_qty} คัน<br>${esc(r.reason)}</span></div><em>${r.level}</em></div>`).join('')||'<div class="empty">ยังไม่มีข้อมูลเพียงพอสำหรับเสนอแนะ</div>'}</div></article></div><div class="executive-summary"><div><span>EXECUTIVE BRIEF</span><h3>ประเด็นสำคัญสำหรับการประชุม</h3></div><ol><li>${best?`${esc(best.model)} เป็นรุ่นนำของช่วงนี้ ขายสำเร็จ ${best.sold_count} คัน`:'ยังไม่มีรถขายสำเร็จในช่วงที่เลือก'}</li><li>${priority?`มี ${priority} รุ่นที่ควรตรวจแผนเติมรถก่อนตัดสินใจสั่งเพิ่ม`:'สต็อกปัจจุบันยังไม่มีสัญญาณเร่งด่วนจากเกณฑ์ยอดขาย'}</li><li>ควรพิจารณาความต้องการลูกค้า ระยะเวลาส่งมอบ และงบประมาณร่วมกับข้อมูลนี้</li></ol></div></section>`}function executivePeriod(period){executiveDashboard(period)}window.executivePeriod=executivePeriod;
async function bookings(){if(state.user?.role!=='employee')return login();setNav(menuFor('employee'),'bookings');const d=await api('/api/employee/bookings');app.innerHTML=`<section class="section"><div class="section-head"><div><h2>จอง / ชำระเงิน</h2><p>ตรวจหลักฐานก่อนยืนยันทุกครั้ง</p></div></div><div class="panel"><h3>หลักฐานรอตรวจ</h3><div class="table-wrap"><table><thead><tr><th>ใบที่</th><th>รายการ</th><th>ประเภท</th><th>จำนวน</th><th>อ้างอิง</th><th>จัดการ</th></tr></thead><tbody>${d.payments.filter(p=>p.status==='Pending').map(p=>`<tr><td>#${p.payment_id}</td><td>#${p.request_id}</td><td>${p.purpose==='Deposit'?(d.bookings.find(r=>r.request_id===p.request_id)?.order_type==='direct'?'ราคารถเต็มจำนวน':'ค่าจอง'):'ยอดคงเหลือ'}</td><td>${baht(p.amount)}</td><td>${esc(p.reference)}</td><td><button class="btn dark" onclick="openSlip(${p.payment_id})">ดูสลิป</button> <button class="btn green" onclick="review(${p.payment_id},true)">ยืนยัน</button> <button class="btn red" onclick="review(${p.payment_id},false)">ปฏิเสธ</button></td></tr>`).join('')||'<tr><td colspan="6" class="empty">ไม่มีหลักฐานรอตรวจ</td></tr>'}</tbody></table></div></div>${bookingTable(d.bookings)}</section>`}
async function review(id,approve){const note=approve?'ตรวจหลักฐานแล้ว':'หลักฐานไม่ถูกต้อง กรุณาส่งใหม่';try{await api('/api/payments/review',{method:'POST',body:JSON.stringify({payment_id:id,approve,note})});toast(approve?'ยืนยันหลักฐานแล้ว':'ปฏิเสธหลักฐานแล้ว');bookings()}catch(x){toast(x.message,true)}}window.review=review;
function openSlip(id){modal(`<h2>หลักฐานการชำระเงิน</h2><img src="/api/payment-image?id=${id}" style="width:100%;max-height:70vh;object-fit:contain;background:#edf2f5">`)}
window.openSlip=openSlip;
async function inventory(){if(state.user?.role!=='employee')return login();setNav(menuFor('employee'),'inventory');const rows=await api('/api/employee/inventory');app.innerHTML=`<section class="section"><div class="section-head"><div><h2>รถยนต์</h2><p>เพิ่มหรือแก้ไขรถทางซ้าย และดูสถานะจากฐานข้อมูลจริง</p></div><button class="btn" onclick="carForm()">+ เพิ่มรถใหม่</button></div><div class="table-wrap"><table><thead><tr><th>รหัส</th><th>รุ่นรถ</th><th>ซีรีส์</th><th>ปี</th><th>สี</th><th>ราคา</th><th>สถานะ</th><th>จัดการ</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${r.car_id}</td><td>${esc(r.model)}</td><td>${esc(r.series)}</td><td>${r.year}</td><td>${esc(r.color)}</td><td>${baht(r.price)}</td><td>${badge(r.status)}</td><td><button class="btn dark" onclick="carForm(${r.car_id})">แก้ไข</button> ${r.status==='Available'?`<button class="btn red" onclick="removeCar(${r.car_id})">ลบ</button>`:'-'}</td></tr>`).join('')}</tbody></table></div></section>`}
async function dataUrl(file){if(!file)return '';return new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.onerror=reject;r.readAsDataURL(file)})}
async function carForm(id=null){
  const c=id?await api('/api/car?id='+id):{model:'',series:'1 Series',year:new Date().getFullYear(),color:'',price:'',description:''};
  const quantityField=id?'':`<div class="field"><label>จำนวนรถเริ่มต้น (คัน)</label><input type="number" name="quantity" min="1" max="100" value="1" required><small>ระบบจะเพิ่มเป็นรถพร้อมขายตามจำนวนนี้</small></div>`;
  modal(`<div class="car-form-header"><span>BMW INVENTORY</span><h2>${id?'แก้ไขข้อมูลรถ':'เพิ่มรถใหม่'}</h2><p>${id?'ปรับปรุงข้อมูลรถที่เลือก':'กรอกข้อมูลรถและจำนวนที่ต้องการเพิ่มเข้าสต๊อก'}</p></div><form id="carForm" class="form-grid car-form-body"><div class="form-section-label wide"><b>01</b><span>ข้อมูลรถ</span></div><div class="field"><label>รุ่นรถ</label><input name="model" value="${esc(c.model)}" placeholder="เช่น BMW 320d M Sport" required></div><div class="field"><label>ซีรีส์</label><select name="series">${['1 Series','2 Series','3 Series','4 Series','5 Series','7 Series','8 Series','X1','X2','X3','X4','X5','X6','X7','i4','i5','i7','iX','Z4'].map(x=>`<option ${x===c.series?'selected':''}>${x}</option>`).join('')}</select></div><div class="field"><label>ปี</label><input type="number" name="year" value="${esc(c.year)}" required></div><div class="field"><label>สี</label><input name="color" value="${esc(c.color)}" placeholder="เช่น Alpine White" required></div><div class="field"><label>ราคา (บาท)</label><input type="number" name="price" min="1" value="${esc(c.price)}" placeholder="0" required></div>${quantityField}<div class="field wide"><label>รายละเอียดรถ</label><textarea name="description" rows="3" placeholder="รายละเอียดและจุดเด่นของรถ" required>${esc(c.description)}</textarea></div><div class="form-section-label wide"><b>02</b><span>รูปภาพรถ</span></div><div class="car-image-grid wide"><div class="field"><label>รูปหลัก ${id?'(ไม่เลือก = ใช้รูปเดิม)':'*'}</label><input type="file" name="image" accept="image/*" ${id?'':'required'}></div><div class="field"><label>รูปด้านหลัง</label><input type="file" name="image2" accept="image/*"></div><div class="field"><label>รูปภายใน</label><input type="file" name="image3" accept="image/*"></div></div><div class="car-form-actions wide"><button type="button" class="btn ghost" onclick="closeModal()">ยกเลิก</button><button class="btn green">${id?'บันทึกการแก้ไข':'เพิ่มรถเข้าสต๊อก'}</button></div></form>`);
  document.querySelector('#carForm').onsubmit=async e=>{e.preventDefault();const fd=new FormData(e.target),payload=Object.fromEntries(fd);payload.car_id=id;for(const n of ['',2,3]){const f=e.target['image'+n].files[0];payload['image'+n]=await dataUrl(f);payload['image_name'+n]=f?.name||''}try{const result=await api('/api/cars/save',{method:'POST',body:JSON.stringify(payload)});closeModal();toast(id?'บันทึกการแก้ไขแล้ว':`เพิ่มรถพร้อมขาย ${result.quantity} คันแล้ว`);inventory()}catch(x){toast(x.message,true)}}
}
window.carForm=carForm;async function removeCar(id){if(!confirm('ลบรถคันนี้หรือไม่? รถที่มีประวัติจะไม่สามารถลบได้'))return;try{await api('/api/cars/delete',{method:'POST',body:JSON.stringify({car_id:id})});toast('ลบรถแล้ว');inventory()}catch(x){toast(x.message,true)}}window.removeCar=removeCar;
async function customers(){if(state.user?.role!=='employee')return login();setNav(menuFor('employee'),'customers');const rows=await api('/api/employee/customers');app.innerHTML=`<section class="section"><div class="section-head"><div><h2>ข้อมูลลูกค้า</h2><p>ข้อมูลสำหรับติดต่อเกี่ยวกับการจองเท่านั้น</p></div></div><div class="table-wrap"><table><thead><tr><th>รหัส</th><th>ชื่อ–นามสกุล</th><th>โทรศัพท์</th><th>อีเมล</th><th>ที่อยู่</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${r.customer_id}</td><td>${esc(r.fname)} ${esc(r.lname)}</td><td>${esc(r.phone)}</td><td>${esc(r.email)}</td><td>${esc(r.address)}</td></tr>`).join('')}</tbody></table></div></section>`}
async function executiveInventory(){if(state.user?.role!=='executive')return login();setNav(menuFor('executive'),'exec-inventory');const rows=await api('/api/executive/inventory'),count=status=>rows.filter(r=>r.status===status).length,availableValue=rows.filter(r=>r.status==='Available').reduce((a,r)=>a+Number(r.price),0);app.innerHTML=`<section class="section executive-subpage"><div class="subpage-hero"><div><div class="exec-kicker"><span>BMW</span><i></i> INVENTORY CONTROL</div><h1>ภาพรวมรถยนต์</h1><p>มุมมองสำหรับผู้บริหาร • อ่านข้อมูลอย่างเดียว</p></div><div class="subpage-total"><small>รถทั้งหมด</small><strong>${rows.length}</strong><span>คัน</span></div></div><div class="exec-kpis compact"><article class="exec-kpi primary"><span>รถพร้อมขาย</span><strong>${count('Available')} <small>คัน</small></strong><small>มูลค่ารวม ${baht(availableValue)}</small></article><article class="exec-kpi"><span>รถถูกจอง</span><strong>${count('Reserved')} <small>คัน</small></strong><small>อยู่ระหว่างขั้นตอนการจอง</small></article><article class="exec-kpi"><span>รถขายแล้ว</span><strong>${count('Sold')} <small>คัน</small></strong><small>มีรายการขายในระบบ</small></article><article class="exec-kpi"><span>รถสถานะอื่น</span><strong>${rows.length-count('Available')-count('Reserved')-count('Sold')} <small>คัน</small></strong><small>ตรวจรายละเอียดในตาราง</small></article></div><div class="executive-table-card"><header><div><span>VEHICLE INVENTORY</span><h3>รายการรถแต่ละคัน</h3></div><div class="executive-search"><input id="execInventorySearch" placeholder="ค้นหารุ่น ซีรีส์ หรือสี"><select id="execInventoryStatus"><option value="">ทุกสถานะ</option><option value="Available">พร้อมขาย</option><option value="Reserved">ถูกจอง</option><option value="Sold">ขายแล้ว</option></select></div></header><div class="table-wrap"><table><thead><tr><th>รหัส</th><th>รุ่นรถ</th><th>ซีรีส์</th><th>ปี</th><th>สี</th><th>ราคา</th><th>สถานะ</th></tr></thead><tbody id="execInventoryBody"></tbody></table></div></div></section>`;const draw=()=>{const q=document.querySelector('#execInventorySearch').value.toLowerCase(),status=document.querySelector('#execInventoryStatus').value,found=rows.filter(r=>(r.model+' '+r.series+' '+r.color).toLowerCase().includes(q)&&(!status||r.status===status));document.querySelector('#execInventoryBody').innerHTML=found.map(r=>`<tr><td><b>#${r.car_id}</b></td><td><strong>${esc(r.model)}</strong></td><td>${esc(r.series)}</td><td>${r.year}</td><td>${esc(r.color)}</td><td>${baht(r.price)}</td><td>${badge(r.status)}</td></tr>`).join('')||'<tr><td colspan="7" class="empty">ไม่พบรถตามเงื่อนไข</td></tr>'};document.querySelector('#execInventorySearch').oninput=draw;document.querySelector('#execInventoryStatus').onchange=draw;draw()}
async function executiveSales(){if(state.user?.role!=='executive')return login();setNav(menuFor('executive'),'exec-sales');const rows=await api('/api/executive/sales'),completed=rows.filter(r=>r.status==='Completed'),cancelled=rows.filter(r=>r.status==='Cancelled'),revenue=completed.reduce((a,r)=>a+Number(r.sale_price),0),average=completed.length?revenue/completed.length:0;app.innerHTML=`<section class="section executive-subpage"><div class="subpage-hero"><div><div class="exec-kicker"><span>BMW</span><i></i> SALES PERFORMANCE</div><h1>ประวัติยอดขาย</h1><p>ติดตามผลการขายและผู้รับผิดชอบแต่ละรายการ</p></div><div class="subpage-total"><small>รายได้จากรายการสำเร็จ</small><strong>${baht(revenue)}</strong></div></div><div class="exec-kpis compact"><article class="exec-kpi primary"><span>ขายสำเร็จ</span><strong>${completed.length} <small>คัน</small></strong><small>ไม่นับรายการยกเลิก</small></article><article class="exec-kpi"><span>มูลค่าเฉลี่ย</span><strong>${baht(average)}</strong><small>ต่อรายการขายสำเร็จ</small></article><article class="exec-kpi"><span>รายการยกเลิก</span><strong>${cancelled.length} <small>รายการ</small></strong><small>เก็บไว้เพื่อการตรวจสอบ</small></article><article class="exec-kpi"><span>รายการทั้งหมด</span><strong>${rows.length} <small>รายการ</small></strong><small>รวมทุกสถานะ</small></article></div><div class="executive-table-card"><header><div><span>TRANSACTION HISTORY</span><h3>รายการขายย้อนหลัง</h3></div></header><div class="table-wrap"><table><thead><tr><th>เลขที่</th><th>วันที่</th><th>ลูกค้า</th><th>รุ่นรถ</th><th>พนักงานผู้ดูแล</th><th>ราคา</th><th>สถานะ</th></tr></thead><tbody>${rows.map(r=>`<tr><td><b>#${r.sale_id}</b></td><td>${esc(r.sale_date)}</td><td>${esc(r.customer)}</td><td><strong>${esc(r.model)}</strong></td><td>${esc(r.staff_name||'-')}</td><td>${baht(r.sale_price)}</td><td>${badge(r.status)}</td></tr>`).join('')||'<tr><td colspan="7" class="empty">ยังไม่มีรายการขาย</td></tr>'}</tbody></table></div></div></section>`}async function profile(){if(state.user?.role!=='customer')return login();setNav([['customer','สรุปของฉัน'],['catalog','เลือกรถ'],['orders','การจอง / สั่งซื้อ'],['profile','ข้อมูลของฉัน']],'profile');const c=await api('/api/customer/profile');app.innerHTML=`<section class="section"><div class="section-head"><div><h2>ข้อมูลของฉัน</h2><p>ใช้ข้อมูลนี้ในเอกสารและการติดต่อเกี่ยวกับการจอง</p></div></div><form id="profileForm" class="panel form-grid"><div class="field"><label>ชื่อ</label><input name="fname" value="${esc(c.fname)}" required></div><div class="field"><label>นามสกุล</label><input name="lname" value="${esc(c.lname)}" required></div><div class="field"><label>เบอร์โทร</label><input name="phone" value="${esc(c.phone)}" required></div><div class="field"><label>อีเมล</label><input type="email" name="email" value="${esc(c.email)}" required></div><div class="field wide"><label>ที่อยู่</label><textarea name="address" required>${esc(c.address)}</textarea></div><button class="btn green wide">บันทึกข้อมูล</button></form></section>`;document.querySelector('#profileForm').onsubmit=async e=>{e.preventDefault();try{await api('/api/customer/profile',{method:'POST',body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});toast('บันทึกข้อมูลแล้ว');await refreshSession()}catch(x){toast(x.message,true)}}}async function sales(){if(state.user?.role!=='employee')return login();setNav(menuFor('employee'),'sales');const rows=await api('/api/employee/sales');app.innerHTML=`<section class="section"><div class="section-head"><div><h2>รายการขาย</h2><p>ประวัติการขายที่ยืนยันแล้ว</p></div></div><div class="table-wrap"><table><thead><tr><th>เลขที่</th><th>วันที่</th><th>ลูกค้า</th><th>รุ่นรถ</th><th>พนักงาน</th><th>ราคา</th><th>สถานะ</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${r.sale_id}</td><td>${esc(r.sale_date)}</td><td>${esc(r.customer)}</td><td>${esc(r.model)}</td><td>${esc(r.staff_name||'-')}</td><td>${baht(r.sale_price)}</td><td>${badge(r.status)}</td></tr>`).join('')||'<tr><td colspan="7" class="empty">ยังไม่มีรายการขาย</td></tr>'}</tbody></table></div></section>`}
async function route(){await refreshSession();const page=location.hash.slice(1)||'catalog';try{if(page==='login')return login();if(page==='customer')return customer();if(page==='orders')return orders();if(page==='profile')return profile();if(page==='executive')return executiveDashboard();if(page==='exec-inventory')return executiveInventory();if(page==='exec-sales')return executiveSales();if(page==='exec-employees')return executiveEmployees();if(page==='bookings')return bookings();if(page==='inventory')return inventory();if(page==='customers')return customers();if(page==='visitors')return employeeVisitors();if(page==='sales')return sales();return catalog()}catch(x){toast(x.message,true);app.innerHTML=`<div class="empty"><h2>เปิดหน้าไม่ได้</h2><p>${esc(x.message)}</p></div>`}}
window.addEventListener('hashchange',route);route();


/* ===== login-fix.js ===== */
window.login=async function(){
  setNav([],null);
  app.innerHTML=`<section class="auth"><form class="auth-card" id="loginForm"><div class="eyebrow">BMW ACCOUNT</div><h1>เข้าสู่ระบบ</h1><p>เลือกประเภทบัญชีให้ตรงกับผู้ใช้งาน</p><div class="role-switch two-roles"><button type="button" class="on" data-role="customer">ลูกค้า</button><button type="button" data-role="employee">พนักงาน</button></div><div class="field"><label>ชื่อผู้ใช้</label><input name="username" required></div><div class="field"><label>รหัสผ่าน</label><input type="password" name="password" required></div><button class="btn full" id="loginButton">เข้าสู่ระบบ</button><button type="button" class="btn ghost full" style="margin-top:8px" onclick="register()">ลงทะเบียนลูกค้าใหม่</button><button type="button" class="btn ghost full" style="margin-top:8px" onclick="resetForm()">ลืมรหัสผ่าน</button></form></section>`;
  document.querySelectorAll('.role-switch button').forEach(button=>button.onclick=()=>{
    document.querySelectorAll('.role-switch button').forEach(item=>item.classList.remove('on'));
    button.classList.add('on');state.role=button.dataset.role;
  });
  document.querySelector('#loginForm').onsubmit=async event=>{
    event.preventDefault();
    const button=document.querySelector('#loginButton');
    const data=Object.fromEntries(new FormData(event.target));
    data.role=state.role;button.disabled=true;button.textContent='กำลังเข้าสู่ระบบ…';
    try{
      await api('/api/login',{method:'POST',body:JSON.stringify(data)});
      const target=data.role==='employee'?'dashboard':'customer';
      if(location.hash.slice(1)===target)await route();else location.hash=target;
    }catch(error){
      button.disabled=false;button.textContent='เข้าสู่ระบบ';toast(error.message,true);
    }
  };
};

window.resetForm=function(){
  modal(`<h2>ตั้งรหัสผ่านลูกค้าใหม่</h2><p>ยืนยันด้วยเบอร์โทรและอีเมลที่บันทึกไว้</p><form id="resetForm" class="form-grid"><input type="hidden" name="role" value="customer"><div class="field wide"><label>ชื่อผู้ใช้ลูกค้า</label><input name="username" required></div><div class="field"><label>เบอร์โทร</label><input name="phone" required></div><div class="field"><label>อีเมล</label><input type="email" name="email" required></div><div class="field wide"><label>รหัสผ่านใหม่อย่างน้อย 8 ตัว</label><input type="password" name="password" minlength="8" required></div><button class="btn wide">ตั้งรหัสผ่านใหม่</button></form>`);
  document.querySelector('#resetForm').onsubmit=async event=>{event.preventDefault();try{await api('/api/reset-password',{method:'POST',body:JSON.stringify(Object.fromEntries(new FormData(event.target)))});closeModal();toast('ตั้งรหัสผ่านใหม่แล้ว')}catch(error){toast(error.message,true)}};
};

if(location.hash==='#login')window.login();


/* ===== payment-ui.js ===== */
// ส่วนหน้าชำระเงิน: แสดง QR และรับสลิปจากลูกค้า
function paymentForm(payment) {
  const paymentName = payment.label || (payment.purpose === 'Deposit' ? 'ค่าจอง' : 'ยอดคงเหลือ');
  modal(`
    <div class="payment-heading">
      <div><span>BMW SECURE PAYMENT</span><h2>ชำระ${paymentName}</h2><p>สแกน QR แล้วแนบสลิปเพื่อให้พนักงานตรวจสอบ</p></div>
      <strong>${baht(payment.amount)}</strong>
    </div>
    <div class="payment-layout">
      <section class="qr-panel"><img src="/payment-qr.jpg" alt="QR Code สำหรับชำระเงิน"><small>กรุณาตรวจสอบยอดก่อนชำระ</small></section>
      <form id="payForm" class="slip-form">
        <h3>แนบหลักฐานการชำระเงิน</h3>
        <div class="field"><label>เลือกรูปสลิป JPG / PNG / WEBP</label><input type="file" name="slip" accept="image/jpeg,image/png,image/webp" required></div>
        <div class="slip-preview" id="slipPreview"><span>ตัวอย่างสลิปจะแสดงตรงนี้</span></div>
        <button class="btn green full">ส่งสลิปให้พนักงานตรวจ</button>
      </form>
    </div>`);
  const form = document.querySelector('#payForm');
  const fileInput = form.slip;
  const preview = document.querySelector('#slipPreview');
  fileInput.onchange = () => {
    const file = fileInput.files[0];
    if (!file) return preview.innerHTML = '<span>ตัวอย่างสลิปจะแสดงตรงนี้</span>';
    const previewUrl = URL.createObjectURL(file);
    preview.innerHTML = `<img src="${previewUrl}" alt="ตัวอย่างสลิป"><small>${esc(file.name)}</small>`;
  };
  form.onsubmit = async event => {
    event.preventDefault();
    const file = fileInput.files[0];
    if (!file) return toast('กรุณาเลือกรูปสลิป', true);
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const transferredAt = new Date().toLocaleString('sv-SE').replace('T', ' ');
        const automaticReference = 'WEB-' + payment.id + '-' + Date.now();
        await api('/api/payments', {method: 'POST', body: JSON.stringify({request_id: payment.id, purpose: payment.purpose, amount: payment.amount, slip: reader.result, slip_name: file.name, transferred_at: transferredAt, reference: automaticReference})});
        closeModal();
        toast('ส่งสลิปให้พนักงานตรวจแล้ว');
        orders();
      } catch (error) { toast(error.message, true); }
    };
    reader.readAsDataURL(file);
  };
}
window.paymentForm = paymentForm;

/* ===== purchase-options.js ===== */
// ตัวเลือกการทำรายการ: จองรถด้วยค่าจอง หรือสั่งซื้อและชำระเต็มจำนวน
function purchaseStatus(record) {
  if (record.status === 'AwaitingPayment' && record.last_payment_status === 'Rejected') return 'สลิปไม่ผ่าน กรุณาส่งใหม่';
  if (record.order_type !== 'direct') return statusLabel[record.status] || record.status;
  return {AwaitingPayment:'รอชำระราคารถ',PaymentReview:'รอตรวจสอบสลิป',Booked:'ยืนยันการชำระแล้ว',Completed:'ซื้อสำเร็จ'}[record.status] || statusLabel[record.status] || record.status;
}
function purchaseBadge(record) {
  const status = record.status;
  const style = ['Completed','Booked'].includes(status)?'green':['Cancelled','Unavailable'].includes(status)?'red':['AwaitingPayment','PaymentReview','CancelRequested'].includes(status)?'gold':'';
  return `<span class="badge ${style}">${esc(purchaseStatus(record))}</span>`;
}
function bookSelected(){
  if(!state.selectedColor)return toast('ไม่มีสีที่พร้อมขาย',true);
  modal(`<div class="purchase-head"><span>BMW PURCHASE OPTIONS</span><h2>เลือกวิธีดำเนินการ</h2><p>เลือกจองไว้ก่อน หรือสั่งซื้อและชำระราคารถเต็มจำนวน</p></div>
    <form id="bookForm" class="form-grid">
      <div class="purchase-choice wide">
        <label><input type="radio" name="order_type" value="booking" checked><span><b>จองรถ</b><small>ชำระค่าจอง 10,000 บาทก่อน แล้วชำระยอดคงเหลือภายหลัง</small></span></label>
        <label><input type="radio" name="order_type" value="direct"><span><b>สั่งซื้อทันที</b><small>ชำระราคารถเต็มจำนวนครั้งเดียว พร้อมส่งสลิปให้พนักงานตรวจ</small></span></label>
      </div>
      <div class="field"><label>รูปแบบการซื้อ</label><select name="purchase_method"><option value="cash">ซื้อเงินสด</option><option value="finance">ขอสินเชื่อ</option></select></div>
      <div class="field"><label>วันที่คาดว่าจะรับรถ</label><input type="date" name="delivery_date"></div>
      <label class="wide terms"><input type="checkbox" name="terms" required> ยอมรับเงื่อนไขและยืนยันข้อมูลการทำรายการ</label>
      <button class="btn green wide" id="purchaseSubmit">ยืนยันจองรถ</button>
    </form>`);
  const form=document.querySelector('#bookForm'),submit=document.querySelector('#purchaseSubmit');
  form.querySelectorAll('[name="order_type"]').forEach(input=>input.onchange=()=>submit.textContent=input.value==='direct'?'ยืนยันสั่งซื้อทันที':'ยืนยันจองรถ');
  form.onsubmit=async event=>{
    event.preventDefault();const data=Object.fromEntries(new FormData(form));data.car_id=state.selectedColor;data.terms_accepted=!!data.terms;
    try{const result=await api('/api/bookings',{method:'POST',body:JSON.stringify(data)});closeModal();toast(data.order_type==='direct'?`สร้างคำสั่งซื้อ #${result.request_id} แล้ว กรุณาชำระราคารถ`:`จองรถสำเร็จ เลขที่ ${result.request_id}`);location.hash='orders';route()}catch(error){toast(error.message,true)}
  };
}
function bookingActions(record,customerView){
  if(customerView){
    let output='';
    if(record.status==='AwaitingPayment'){
      const direct=record.order_type==='direct';
      output+=`<button class="btn ${direct?'green':''}" onclick='paymentForm(${JSON.stringify({id:record.request_id,amount:record.deposit_amount,purpose:'Deposit',label:direct?'ราคารถเต็มจำนวน':'ค่าจอง'})})'>${direct?'ชำระราคารถ':'ชำระค่าจอง'}</button>`;
    }
    if(record.status==='Booked'&&Number(record.remaining_amount)>0)output+=`<button class="btn green" onclick='paymentForm(${JSON.stringify({id:record.request_id,amount:record.remaining_amount,purpose:'Balance',label:'ยอดคงเหลือ'})})'>ชำระยอดคงเหลือ</button>`;
    if(['AwaitingPayment','PaymentReview','Booked'].includes(record.status))output+=` <button class="btn red" onclick="cancelBooking(${record.request_id},false)">ขอยกเลิก</button>`;
    return output||'-';
  }
  let output='';
  if(record.status==='Booked'&&Number(record.remaining_amount)===0)output+=`<button class="btn green" onclick="confirmSale(${record.request_id})">ยืนยันขาย</button>`;
  if(record.status==='CancelRequested')output+=`<button class="btn red" onclick="cancelBooking(${record.request_id},true)">อนุมัติยกเลิก</button>`;
  return output||'-';
}
function bookingTable(rows,customerView=false){
  return `<div class="panel"><h3>${customerView?'รายการจองและสั่งซื้อของฉัน':'รายการจองและสั่งซื้อ'}</h3><div class="table-wrap"><table><thead><tr><th>เลขที่</th><th>ประเภท</th><th>ลูกค้า</th><th>รุ่น / สี</th><th>ชำระแล้ว</th><th>คงเหลือ</th><th>สถานะ</th><th>จัดการ</th></tr></thead><tbody>${rows.map(r=>`<tr><td>#${r.request_id}</td><td><b>${r.order_type==='direct'?'สั่งซื้อทันที':'จองรถ'}</b></td><td>${esc(r.customer)}</td><td>${esc(r.model)}<br><small>${esc(r.color)}</small></td><td>${baht(r.paid_amount)}</td><td>${baht(r.remaining_amount)}</td><td>${purchaseBadge(r)}</td><td class="actions">${bookingActions(r,customerView)}</td></tr>`).join('')||'<tr><td colspan="8" class="empty">ยังไม่มีรายการ</td></tr>'}</tbody></table></div></div>`;
}
window.bookSelected=bookSelected;window.bookingActions=bookingActions;window.bookingTable=bookingTable;


/* ===== customer-simplify.js ===== */
// ขั้นตอนลูกค้าแบบเดียว: เลือกรถ > สั่งซื้อเงินสด > ส่งสลิป > ติดตามสถานะ
if(typeof window.visitorDate!=='function')window.visitorDate=value=>{const raw=String(value||'').trim(),parts=raw.split(' '),date=(parts[0]||'').split('-');return date.length===3?`${date[2]}/${date[1]}/${date[0]} ${parts[1]||''}`.trim():raw||'-'};
window.menuFor=function(role){
  if(role==='customer')return [['customer','สรุปและรายการสั่งซื้อ'],['catalog','เลือกรถ'],['profile','ข้อมูลของฉัน']];
  if(role==='employee')return [['bookings','สั่งซื้อ / ชำระเงิน'],['inventory','รถยนต์'],['customers','ข้อมูลลูกค้า'],['visitors','ผู้เข้าชม'],['sales','รายการขาย']];
  return [['catalog','เลือกรถ']];
};

Object.assign(statusLabel,{AwaitingPayment:'รอชำระเงิน',PaymentReview:'รอตรวจสอบสลิป',Booked:'ยืนยันการชำระแล้ว'});

window.hero=function(){return `<section class="hero hero-clean"><div class="hero-copy"><div class="eyebrow">Sheer Driving Pleasure</div><h1>ค้นพบ BMW<br>ที่ใช่สำหรับคุณ</h1><p>สัมผัสรถยนต์ระดับพรีเมียม</p><button class="btn" onclick="document.querySelector('#catalog').scrollIntoView()">สำรวจรถทั้งหมด</button></div></section>`};

window.catalog=async function(){
  if(!state.visitor&&!state.user)return visitorGate();
  await loadCars();setNav(state.user?menuFor(state.user.role):[['catalog','เลือกรถ']],'catalog');
  const series=[...new Set(state.cars.map(car=>car.series))];
  app.innerHTML=hero()+`<section class="section" id="catalog"><div class="section-head"><div><h2>BMW รุ่นรถ</h2><p>เลือกรุ่นและสีที่ต้องการสั่งซื้อ</p></div></div><div class="toolbar"><input id="search" placeholder="ค้นหารุ่นรถหรือซีรีส์"></div><div class="catalog-layout"><aside class="filters"><button class="on" data-series="">รถทั้งหมด</button><h3>Series</h3>${series.map(item=>`<button data-series="${esc(item)}">${esc(item)}</button>`).join('')}</aside><div class="grid" id="carGrid"></div></div></section>`;
  const draw=(query='',selectedSeries='')=>{
    const cars=state.cars.filter(car=>(car.model+' '+car.series).toLowerCase().includes(query.toLowerCase())&&(!selectedSeries||car.series===selectedSeries));
    document.querySelector('#carGrid').innerHTML=cars.map(car=>{const soldOut=car.colors.every(color=>Number(color.quantity)===0);return `<article class="car-card ${soldOut?'sold-out':''}"><img loading="lazy" src="/api/car-image?id=${car.car_id}&slot=1"><div class="car-body"><div class="series">BMW • ${esc(car.series)}</div><h3>${esc(car.model)}</h3><div>${car.year}${soldOut?' • <span class="stock-out">สินค้าหมด</span>':''}</div><div class="price">${baht(car.price)}</div><div class="card-actions"><button class="btn dark" onclick="openCar(${car.car_id})">ดูรายละเอียด</button>${state.user?.role==='customer'&&!soldOut?`<button class="btn" onclick="openCar(${car.car_id},true)">สั่งซื้อ</button>`:''}</div></div></article>`}).join('')||'<div class="empty">ไม่พบรถที่ค้นหา</div>';
  };
  draw();document.querySelector('#search').oninput=event=>draw(event.target.value,document.querySelector('.filters .on').dataset.series);
  document.querySelectorAll('.filters button').forEach(button=>button.onclick=()=>{document.querySelectorAll('.filters button').forEach(item=>item.classList.remove('on'));button.classList.add('on');draw(document.querySelector('#search').value,button.dataset.series)});
};

window.openCar=async function(id,buy=false){
  const car=await api('/api/car?id='+id),available=car.colors.filter(color=>Number(color.quantity)>0);
  setNav(state.user?menuFor(state.user.role):[['catalog','เลือกรถ']],'catalog');
  app.innerHTML=`<section class="section"><button class="btn ghost" onclick="location.hash='catalog'">← กลับไปดูรถ</button><div class="detail"><div><img id="mainPhoto" class="gallery-main" src="/api/car-image?id=${car.car_id}&slot=1"><div class="thumbs">${[1,2,3].map(slot=>`<img src="/api/car-image?id=${car.car_id}&slot=${slot}" onerror="this.style.display='none'" onclick="mainPhoto.src=this.src">`).join('')}</div></div><div><div class="eyebrow">${esc(car.series)}</div><h1>${esc(car.model)}</h1><p>${car.year}</p><div class="price">${baht(car.price)}</div><h3>เลือกสีรถ</h3><div class="colors">${car.colors.map(color=>`<button class="color-choice ${Number(color.quantity)>0&&color.car_id===available[0]?.car_id?'on':''}" data-id="${color.car_id}" ${Number(color.quantity)===0?'disabled':''} onclick="chooseColor(this)">${esc(color.color)}${Number(color.quantity)===0?' • สินค้าหมด':''}</button>`).join('')}</div><p>${esc(car.description||'รายละเอียดรถยนต์ BMW ที่คัดสรรสำหรับคุณ')}</p>${available.length?(state.user?.role==='customer'?'<button class="btn full" onclick="bookSelected()">สั่งซื้อรถคันนี้</button>':'<button class="btn full" onclick="location.hash=\'login\'">เข้าสู่ระบบก่อนสั่งซื้อ</button>'):'<div class="stock-out-box">รถรุ่นนี้สินค้าหมด</div>'}</div></div></section>`;
  state.selectedColor=available.length?Number(available[0].car_id):null;if(buy&&state.user?.role==='customer'&&available.length)setTimeout(bookSelected,0);
};

window.bookSelected=function(){
  if(!state.selectedColor)return toast('รถสีนี้หมดแล้ว กรุณาเลือกสีอื่น',true);
  modal(`<div class="purchase-head"><span>BMW PURCHASE</span><h2>ยืนยันการสั่งซื้อ</h2><p>ชำระราคารถเต็มจำนวน พร้อมส่งสลิปให้พนักงานตรวจสอบ</p></div><form id="bookForm" class="form-grid"><label class="wide terms"><input type="checkbox" name="terms" required> ยืนยันข้อมูลและยอมรับเงื่อนไขการสั่งซื้อ</label><button class="btn green wide">ยืนยันสั่งซื้อ</button></form>`);
  document.querySelector('#bookForm').onsubmit=async event=>{event.preventDefault();const data={car_id:state.selectedColor,purchase_method:'cash',order_type:'direct',delivery_date:'',terms_accepted:true};try{const result=await api('/api/bookings',{method:'POST',body:JSON.stringify(data)});closeModal();toast(`สร้างคำสั่งซื้อ #${result.request_id} แล้ว กรุณาชำระราคารถ`);location.hash='customer'}catch(error){toast(error.message,true)}};
};

window.bookingActions=function(record,customerView){
  if(customerView){let output='';if(record.status==='AwaitingPayment')output+=`<button class="btn green" onclick='paymentForm(${JSON.stringify({id:record.request_id,amount:record.remaining_amount||record.deposit_amount,purpose:'Deposit',label:'ราคารถ'})})'>ชำระราคารถ</button>`;if(record.status==='Booked'&&Number(record.remaining_amount)>0)output+=`<button class="btn green" onclick='paymentForm(${JSON.stringify({id:record.request_id,amount:record.remaining_amount,purpose:'Balance',label:'ยอดคงเหลือ'})})'>ชำระยอดคงเหลือ</button>`;if(['AwaitingPayment','PaymentReview','Booked'].includes(record.status))output+=` <button class="btn red" onclick="cancelBooking(${record.request_id},false)">ขอยกเลิก</button>`;return output||'-'}
  let output='';if(record.status==='Booked'&&Number(record.remaining_amount)===0)output+=`<button class="btn green" onclick="confirmSale(${record.request_id})">ยืนยันขาย</button>`;if(record.status==='CancelRequested')output+=`<button class="btn red" onclick="cancelBooking(${record.request_id},true)">อนุมัติยกเลิก</button>`;return output||'-';
};

function orderProgress(record){
  if(record.status==='Cancelled'||record.status==='CancelRequested')return `<div class="order-progress cancelled"><span class="on">สั่งซื้อ</span><span class="on">ขอยกเลิก</span><span class="${record.status==='Cancelled'?'on':''}">ยกเลิกแล้ว</span></div>`;
  const step={AwaitingPayment:0,PaymentReview:1,Booked:2,Completed:2}[record.status]??0;
  return `<div class="order-progress">${['สั่งซื้อ','ส่งสลิป','ซื้อสำเร็จ'].map((label,index)=>`<span class="${index<=step?'on':''} ${index===step?'current':''}">${label}</span>`).join('')}</div>${record.last_payment_status==='Rejected'?`<small class="payment-rejected">${esc(record.last_payment_note||'หลักฐานไม่ผ่าน กรุณาส่งใหม่')}</small>`:''}`;
}

window.bookingTable=function(rows,customerView=false){return `<div class="panel"><h3>${customerView?'รายการสั่งซื้อของฉัน':'รายการสั่งซื้อ'}</h3><div class="table-wrap"><table><thead><tr><th>เลขที่</th><th>ลูกค้า</th><th>รุ่น / สี</th><th>ชำระแล้ว</th><th>ยอดที่ต้องชำระ</th><th>สถานะ</th><th>จัดการ</th></tr></thead><tbody>${rows.map(record=>`<tr><td>#${record.request_id}</td><td>${esc(record.customer)}</td><td>${esc(record.model)}<br><small>${esc(record.color)}</small></td><td>${baht(record.paid_amount)}</td><td>${baht(record.remaining_amount)}</td><td class="status-cell">${purchaseBadge(record)}${customerView?orderProgress(record):''}</td><td class="actions">${bookingActions(record,customerView)}</td></tr>`).join('')||'<tr><td colspan="7" class="empty">ยังไม่มีรายการสั่งซื้อ</td></tr>'}</tbody></table></div></div>`};

window.customer=async function(){if(state.user?.role!=='customer')return login();setNav(menuFor('customer'),'customer');const data=await api('/api/customer/overview'),summary=data.summary;app.innerHTML=`<section class="section"><div class="section-head"><div><h2>สรุปและรายการสั่งซื้อ</h2><p>ดูยอดชำระ สถานะ และดำเนินการทั้งหมดในหน้านี้</p></div><button class="btn" onclick="location.hash='catalog'">เลือกรถ</button></div><div class="stats"><div class="stat"><small>ซื้อสำเร็จ</small><strong>${summary.bought_count} คัน</strong></div><div class="stat"><small>มูลค่ารวม</small><strong>${baht(summary.order_total)}</strong></div><div class="stat"><small>ชำระแล้ว</small><strong>${summary.paid_count} รายการ</strong></div><div class="stat"><small>ยังไม่ชำระครบ</small><strong>${summary.unpaid_count} รายการ</strong></div></div>${bookingTable(data.bookings,true)}</section>`};
window.orders=async function(){if(location.hash==='#customer')return customer();location.hash='customer'};

window.pendingPaymentRows=[];
window.bookings=async function(){
  if(state.user?.role!=='employee')return login();setNav(menuFor('employee'),'bookings');
  const data=await api('/api/employee/bookings');window.pendingPaymentRows=data.payments.filter(payment=>payment.status==='Pending');
  app.innerHTML=`<section class="section staff-order-page"><div class="section-head"><div><h2>สั่งซื้อ / ชำระเงิน</h2><p>ตรวจข้อมูลลูกค้า รายการรถ และหลักฐานก่อนยืนยัน</p></div></div><div class="review-section"><header><div><h3>หลักฐานรอตรวจ</h3><p>เรียงตามรายการที่ส่งเข้ามาล่าสุด</p></div><div class="pending-count"><strong>${pendingPaymentRows.length}</strong><span>รายการ</span></div></header><div class="review-card-list">${pendingPaymentRows.map(payment=>`<article class="payment-review-card"><div class="review-id"><span>รอตรวจ</span><strong>สลิป #${payment.payment_id}</strong><small>คำสั่งซื้อ #${payment.request_id}</small></div><div class="review-customer"><small>ลูกค้า</small><strong>${esc(payment.customer)}</strong><span>${esc(payment.customer_phone)}</span><span>${esc(payment.customer_email)}</span></div><div class="review-car"><small>รถที่สั่งซื้อ</small><strong>${esc(payment.model)}</strong><span>${esc(payment.color)} • ${payment.year}</span></div><div class="review-money"><small>ยอดชำระ</small><strong>${baht(payment.amount)}</strong><span>ส่ง ${esc(visitorDate(payment.created_at))}</span></div><button class="review-open" onclick="openPaymentReview(${payment.payment_id})">เปิดตรวจสอบ <b>→</b></button></article>`).join('')||'<div class="review-empty"><strong>ไม่มีหลักฐานรอตรวจ</strong><span>รายการใหม่จะแสดงในส่วนนี้</span></div>'}</div></div>${bookingTable(data.bookings)}</section>`;
};

window.openPaymentReview=function(paymentId){
  const payment=pendingPaymentRows.find(item=>Number(item.payment_id)===Number(paymentId));if(!payment)return toast('ไม่พบหลักฐานนี้',true);
  modal(`<div class="review-modal-head"><span>ตรวจสอบหลักฐานการชำระเงิน</span><h2>คำสั่งซื้อ #${payment.request_id}</h2></div><div class="review-layout"><div class="review-slip"><img src="/api/payment-image?id=${payment.payment_id}" alt="หลักฐานการชำระเงิน"></div><div class="review-facts"><section><h3>ข้อมูลลูกค้า</h3><dl><dt>ชื่อ–นามสกุล</dt><dd>${esc(payment.customer)}</dd><dt>เบอร์โทร</dt><dd>${esc(payment.customer_phone)}</dd><dt>อีเมล</dt><dd>${esc(payment.customer_email)}</dd></dl></section><section><h3>รายการรถ</h3><dl><dt>รุ่นรถ</dt><dd>${esc(payment.model)}</dd><dt>สี / ปี</dt><dd>${esc(payment.color)} / ${payment.year}</dd></dl></section><section><h3>ข้อมูลการชำระเงิน</h3><dl><dt>ยอดเงิน</dt><dd class="review-amount">${baht(payment.amount)}</dd><dt>เวลาโอน</dt><dd>${esc(visitorDate(payment.transferred_at))}</dd><dt>เวลาอัปโหลด</dt><dd>${esc(visitorDate(payment.created_at))}</dd><dt>เลขอ้างอิง</dt><dd>${esc(payment.reference||'-')}</dd><dt>ชื่อไฟล์</dt><dd>${esc(payment.slip_name)}</dd></dl></section><div class="review-actions"><button class="btn red" onclick="submitPaymentReview(${payment.payment_id},false)">ปฏิเสธหลักฐาน</button><button class="btn green" onclick="submitPaymentReview(${payment.payment_id},true)">ยืนยันการขาย</button></div></div></div>`);
};

window.submitPaymentReview=async function(paymentId,approve){
  const note=approve?'ตรวจสอบข้อมูลลูกค้า ยอดเงิน และหลักฐาน พร้อมยืนยันขายแล้ว':'หลักฐานไม่ถูกต้อง กรุณาส่งใหม่';
  try{await api('/api/payments/review',{method:'POST',body:JSON.stringify({payment_id:paymentId,approve,note})});closeModal();toast(approve?'ยืนยันการขายสำเร็จแล้ว':'ปฏิเสธหลักฐานแล้ว');bookings()}catch(error){toast(error.message,true)}
};


/* ===== employee-dashboard.js ===== */
// แดชบอร์ดยอดขายสำหรับพนักงาน: สรุปจำนวน รายได้ และอันดับรุ่นขายดี
const showroomCatalog=window.catalog;
const showroomMenuFor=window.menuFor;

window.menuFor=function(role){
  if(role==='employee')return [['dashboard','ยอดขาย'],['bookings','สั่งซื้อ / ชำระเงิน'],['inventory','รถยนต์'],['customers','ข้อมูลลูกค้า'],['visitors','ผู้เข้าชม']];
  return showroomMenuFor(role);
};

function salesTabs(active){return `<div class="sales-view-tabs"><button class="${active==='overview'?'on':''}" onclick="employeeSalesDashboard()">ภาพรวม</button><button class="${active==='history'?'on':''}" onclick="employeeSalesHistory()">ประวัติการขาย</button></div>`}

function dashboardMonth(value){
  const [year,month]=String(value).split('-');
  return new Intl.DateTimeFormat('th-TH',{month:'short'}).format(new Date(Number(year),Number(month)-1,1));
}

window.employeeSalesDashboard=async function(){
  if(state.user?.role!=='employee')return login();
  setNav(menuFor('employee'),'dashboard');
  const data=await api('/api/employee/dashboard'),summary=data.summary,ranking=data.ranking||[],monthly=data.monthly||[];
  const topThree=ranking.slice(0,3),maxMonth=Math.max(1,...monthly.map(item=>Number(item.sold_count)));
  app.innerHTML=`<section class="section sales-dashboard">
    <div class="sales-dash-head"><div class="dashboard-title"><span>BMW SALES OVERVIEW</span><h1>แดชบอร์ดยอดขาย</h1><p>ภาพรวมยอดขาย รุ่นยอดนิยม และจำนวนรถพร้อมขาย</p></div><div class="dash-live"><i></i> ข้อมูลล่าสุดจากระบบ</div></div>
    ${salesTabs('overview')}
    <div class="sales-kpis">
      <article class="dark"><small>ขายสำเร็จทั้งหมด</small><strong>${summary.sold_count}</strong><span>คัน</span></article>
      <article><small>ยอดขายรวม</small><strong>${baht(summary.revenue)}</strong><span>รายการที่ยืนยันแล้ว</span></article>
      <article><small>รถพร้อมขาย</small><strong>${summary.available_qty}</strong><span>คัน</span></article>
    </div>
    <div class="dashboard-focus">
      <article class="dash-card top-models-panel"><header><div><h2>รถขายดี 3 อันดับ</h2><p>เรียงจากจำนวนรถที่ขายสำเร็จ</p></div></header>
        ${topThree.length?`<div class="top-model-grid">${topThree.map((item,index)=>`<div class="top-model-card rank-${index+1}"><div class="top-model-rank"><span>อันดับ</span><strong>${index+1}</strong></div><div class="top-model-name"><small>${esc(item.series)}</small><strong>${esc(item.model)}</strong></div><div class="top-model-result"><span>ขายแล้ว</span><strong>${item.sold_count} คัน</strong><small>${baht(item.revenue)}</small></div></div>`).join('')}</div>`:'<div class="dash-empty">ยังไม่มีรายการขายสำเร็จ</div>'}
      </article>
      <article class="dash-card monthly-card"><header><div><h2>ยอดขาย 6 เดือนล่าสุด</h2><p>จำนวนรถที่ขายสำเร็จในแต่ละเดือน</p></div></header>
        <div class="month-chart">${monthly.map(item=>`<div class="month-col"><div class="month-value">${item.sold_count}</div><div class="month-bar"><i style="height:${Number(item.sold_count)?Math.max(12,Number(item.sold_count)/maxMonth*100):3}%"></i></div><span>${dashboardMonth(item.month)}</span></div>`).join('')}</div>
      </article>
    </div>
  </section>`;
};

window.employeeSalesHistory=async function(){
  if(state.user?.role!=='employee')return login();
  setNav(menuFor('employee'),'dashboard');
  const rows=await api('/api/employee/sales');
  app.innerHTML=`<section class="section sales-dashboard">
    <div class="sales-dash-head"><div class="dashboard-title"><span>BMW SALES RECORDS</span><h1>ประวัติการขาย</h1><p>รายการรถที่ยืนยันการขายในระบบ</p></div><div class="dash-live"><i></i> ${rows.length} รายการ</div></div>
    ${salesTabs('history')}
    <article class="dash-card sales-history-card"><header><div><h2>รายการขายทั้งหมด</h2><p>เรียงจากรายการล่าสุด</p></div><b>${rows.length} รายการ</b></header>
      <div class="table-wrap"><table><thead><tr><th>เลขที่</th><th>วันที่</th><th>รถยนต์</th><th>ลูกค้า</th><th>ราคา</th><th>สถานะ</th></tr></thead><tbody>${rows.map(item=>`<tr><td><b>#${item.sale_id}</b></td><td>${esc(item.sale_date||'-')}</td><td><strong>${esc(item.model)}</strong><br><small>${esc(item.color||'-')}</small></td><td>${esc(item.customer||'-')}</td><td><b>${baht(item.sale_price)}</b></td><td>${badge(item.status)}</td></tr>`).join('')||'<tr><td colspan="6" class="empty">ยังไม่มีรายการขาย</td></tr>'}</tbody></table></div>
    </article>
  </section>`;
};

window.sales=window.employeeSalesHistory;

window.catalog=async function(){
  if(location.hash==='#dashboard'&&state.user?.role==='employee')return employeeSalesDashboard();
  return showroomCatalog();
};


/* ===== inventory-ui.js ===== */
// หน้าสต็อกแบบรวมจำนวนตามรุ่นและสี
function sumStock(rows,key){return rows.reduce((sum,row)=>sum+Number(row[key]||0),0)}
async function inventory(){
  if(state.user?.role!=='employee')return login();setNav(menuFor('employee'),'inventory');
  const rows=await api('/api/employee/inventory');
  app.innerHTML=`<section class="section stock-page"><div class="section-head"><div><div class="eyebrow">INVENTORY CONTROL</div><h2>จัดการสต็อกรถยนต์</h2><p>เพิ่มหรือลดจำนวนรถพร้อมขายตามรุ่นและสี ข้อมูลอัปเดตถึงหน้าลูกค้าทันที</p></div><button class="btn" onclick="carForm()">+ เพิ่มรุ่นหรือสีใหม่</button></div>
  <div class="stock-kpis"><article><span>พร้อมขาย</span><strong>${sumStock(rows,'available_qty')}</strong><small>คัน</small></article><article><span>ถูกจอง</span><strong>${sumStock(rows,'reserved_qty')}</strong><small>คัน</small></article><article><span>ขายแล้ว</span><strong>${sumStock(rows,'sold_qty')}</strong><small>คัน</small></article><article><span>รุ่น / สี</span><strong>${rows.length}</strong><small>รายการ</small></article></div>
  <div class="stock-toolbar"><input id="stockSearch" placeholder="ค้นหารุ่น ซีรีส์ หรือสี"><span>กรอกจำนวน แล้วเลือกเพิ่มหรือลดรถพร้อมขาย</span></div>
  <div class="table-wrap stock-table"><table><thead><tr><th>รุ่นรถ</th><th>ซีรีส์ / ปี</th><th>สี</th><th>ราคา</th><th>พร้อมขาย</th><th>ถูกจอง</th><th>ขายแล้ว</th><th>ปรับจำนวน</th><th>รายละเอียด</th></tr></thead><tbody id="stockBody"></tbody></table></div></section>`;
  const draw=()=>{const query=document.querySelector('#stockSearch').value.toLowerCase(),filtered=rows.filter(r=>(r.model+' '+r.series+' '+r.color).toLowerCase().includes(query));document.querySelector('#stockBody').innerHTML=filtered.map(r=>`<tr><td><strong>${esc(r.model)}</strong></td><td>${esc(r.series)}<br><small>${r.year}</small></td><td>${esc(r.color)}</td><td>${baht(r.price)}</td><td><span class="qty available">${r.available_qty} คัน</span></td><td><span class="qty reserved">${r.reserved_qty}</span></td><td><span class="qty sold">${r.sold_qty}</span></td><td><div class="stock-amount"><input id="stockAmount-${r.control_car_id}" type="number" min="1" max="100" value="1" aria-label="จำนวนที่ต้องการปรับ"><button class="add" onclick="adjustStockInput(${r.control_car_id},1)">เพิ่ม</button><button class="remove" onclick="adjustStockInput(${r.control_car_id},-1)">ลด</button></div></td><td><button class="btn dark compact-btn" onclick="carForm(${r.control_car_id})">แก้ไขข้อมูล</button></td></tr>`).join('')||'<tr><td colspan="9" class="empty">ไม่พบรถตามคำค้น</td></tr>'};
  document.querySelector('#stockSearch').oninput=draw;draw();
}
function adjustStockInput(carId,direction){
  const input=document.querySelector(`#stockAmount-${carId}`),amount=Number(input?.value);
  if(!Number.isInteger(amount)||amount<1||amount>100)return toast('กรอกจำนวนเต็มตั้งแต่ 1–100 คัน',true);
  adjustStock(carId,amount*direction);
}
async function adjustStock(carId,delta){
  if(delta<0&&!confirm(`ยืนยันลดรถพร้อมขาย ${Math.abs(delta)} คัน?`))return;
  try{const result=await api('/api/stock/adjust',{method:'POST',body:JSON.stringify({car_id:carId,delta})});toast(`คงเหลือพร้อมขาย ${result.quantity} คัน`);inventory()}catch(error){toast(error.message,true)}
}
async function executiveInventory(){
  if(state.user?.role!=='executive')return login();setNav(menuFor('executive'),'exec-inventory');const rows=await api('/api/executive/inventory');
  const total=sumStock(rows,'total_qty'),available=sumStock(rows,'available_qty'),reserved=sumStock(rows,'reserved_qty'),sold=sumStock(rows,'sold_qty');
  app.innerHTML=`<section class="section executive-subpage"><div class="subpage-hero"><div><div class="exec-kicker"><span>BMW</span><i></i> INVENTORY INTELLIGENCE</div><h1>ภาพรวมสต็อก</h1><p>จำนวนรถจริงแยกตามรุ่นและสี สำหรับวางแผนเติมรถ</p></div><div class="subpage-total"><small>รถทั้งหมด</small><strong>${total}</strong><span>คัน</span></div></div><div class="exec-kpis compact"><article class="exec-kpi primary"><span>พร้อมขาย</span><strong>${available} <small>คัน</small></strong><small>พร้อมให้ลูกค้าจองหรือซื้อ</small></article><article class="exec-kpi"><span>ถูกจอง</span><strong>${reserved} <small>คัน</small></strong><small>อยู่ระหว่างดำเนินการ</small></article><article class="exec-kpi"><span>ขายแล้ว</span><strong>${sold} <small>คัน</small></strong><small>ยอดสะสมในฐานข้อมูล</small></article><article class="exec-kpi"><span>รุ่น / สี</span><strong>${rows.length} <small>รายการ</small></strong><small>กลุ่มสต็อกทั้งหมด</small></article></div><div class="executive-table-card"><header><div><span>LIVE STOCK</span><h3>จำนวนคงเหลือแยกตามรุ่นและสี</h3></div><div class="executive-search"><input id="execStockSearch" placeholder="ค้นหารุ่น ซีรีส์ หรือสี"></div></header><div class="table-wrap"><table><thead><tr><th>รุ่นรถ</th><th>ซีรีส์</th><th>ปี</th><th>สี</th><th>ราคา</th><th>พร้อมขาย</th><th>ถูกจอง</th><th>ขายแล้ว</th><th>รวม</th></tr></thead><tbody id="execStockBody"></tbody></table></div></div></section>`;
  const draw=()=>{const q=document.querySelector('#execStockSearch').value.toLowerCase(),found=rows.filter(r=>(r.model+' '+r.series+' '+r.color).toLowerCase().includes(q));document.querySelector('#execStockBody').innerHTML=found.map(r=>`<tr><td><strong>${esc(r.model)}</strong></td><td>${esc(r.series)}</td><td>${r.year}</td><td>${esc(r.color)}</td><td>${baht(r.price)}</td><td><span class="qty available">${r.available_qty}</span></td><td>${r.reserved_qty}</td><td>${r.sold_qty}</td><td><b>${r.total_qty}</b></td></tr>`).join('')||'<tr><td colspan="9" class="empty">ไม่พบข้อมูล</td></tr>'};document.querySelector('#execStockSearch').oninput=draw;draw();
}
window.inventory=inventory;window.adjustStock=adjustStock;window.adjustStockInput=adjustStockInput;window.executiveInventory=executiveInventory;

/* ===== employee-visitors.js ===== */
function visitorDate(value){
  const raw=String(value||'').trim();
  if(!raw)return '-';
  const parts=raw.split(' '),date=(parts[0]||'').split('-');
  return date.length===3?`${date[2]}/${date[1]}/${date[0]} ${parts[1]||''}`.trim():raw;
}

async function employeeVisitors(){
  if(state.user?.role!=='employee')return login();
  setNav(menuFor('employee'),'visitors');
  const rows=await api('/api/employee/visitors');
  const today=new Date(),todayKey=`${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
  const unique=new Set(rows.map(row=>String(row.phone).replace(/\D/g,''))).size;
  const draw=list=>{
    document.querySelector('#visitorBody').innerHTML=list.map((row,index)=>`<tr>
      <td><span class="visitor-number">${rows.length-index}</span></td>
      <td><strong>${esc(row.name)}</strong></td>
      <td><span class="visitor-phone">${esc(row.phone)}</span></td>
      <td>${esc(visitorDate(row.created_at))}</td>
    </tr>`).join('')||'<tr><td colspan="4" class="empty">ยังไม่มีข้อมูลผู้เข้าชม</td></tr>';
    document.querySelector('#visitorResult').textContent=`แสดง ${list.length} รายการ`;
  };
  app.innerHTML=`<section class="section visitor-page">
    <div class="visitor-heading"><div><span class="visitor-kicker">VISITOR CONTACTS</span><h1>ผู้เข้าชมรถ</h1><p>รายชื่อที่กรอกก่อนเข้าชมรถ เรียงจากล่าสุด</p></div><div class="visitor-live"><i></i> ข้อมูลล่าสุด</div></div>
    <div class="visitor-kpis">
      <article><span>เข้าชมวันนี้</span><strong>${rows.filter(row=>String(row.created_at).startsWith(todayKey)).length}</strong><small>ครั้ง</small></article>
      <article><span>ผู้เข้าชมไม่ซ้ำ</span><strong>${unique}</strong><small>เบอร์โทร</small></article>
      <article><span>ประวัติทั้งหมด</span><strong>${rows.length}</strong><small>รายการ</small></article>
    </div>
    <div class="visitor-card"><header><div><h2>ข้อมูลติดต่อผู้เข้าชม</h2><span id="visitorResult"></span></div><label class="visitor-search"><span>ค้นหา</span><input id="visitorSearch" placeholder="ชื่อหรือเบอร์โทร"></label></header>
      <div class="table-wrap"><table><thead><tr><th>ลำดับ</th><th>ชื่อผู้เข้าชม</th><th>เบอร์โทร</th><th>วันและเวลาที่เข้าชม</th></tr></thead><tbody id="visitorBody"></tbody></table></div>
    </div>
  </section>`;
  draw(rows);
  document.querySelector('#visitorSearch').oninput=event=>{
    const q=event.target.value.trim().toLowerCase();
    draw(rows.filter(row=>(`${row.name} ${row.phone}`).toLowerCase().includes(q)));
  };
}

window.employeeVisitors=employeeVisitors;


/* ===== documents-ui.js ===== */
// ส่วนเอกสาร: ปุ่มเดียวและเลือกชนิดเอกสารตามสถานะให้อัตโนมัติ
(() => {
  const originalBookingActions = window.bookingActions;

  function documentKind(status, orderType) {
    if (status === 'CancelRequested' || status === 'Cancelled' || status === 'Unavailable') return 'status';
    return 'order';
  }

  window.bookingActions = function (record, customerView) {
    const original = originalBookingActions(record, customerView);
    const actions = original === '-' ? '' : original;
    const kind = documentKind(record.status, record.order_type);
    return `${actions} <button class="btn document-btn" onclick="requestDocument(${record.request_id},'${kind}')">ขอเอกสาร</button>`;
  };

  window.requestDocument = function (requestId, kind) {
    window.open(`/api/document?id=${requestId}&kind=${encodeURIComponent(kind)}`, '_blank', 'noopener');
  };
})();
