/* Enough of three.js r128 to boot the atlas without a GPU. Vector3 carries
   real arithmetic because picking depends on it; everything else records that
   it was called and returns something chainable. */
function V3(x,y,z){this.x=x||0;this.y=y||0;this.z=z||0;}
V3.prototype.set=function(x,y,z){this.x=x;this.y=y;this.z=z;return this;};
V3.prototype.clone=function(){return new V3(this.x,this.y,this.z);};
V3.prototype.copy=function(v){this.x=v.x;this.y=v.y;this.z=v.z;return this;};
V3.prototype.sub=function(v){this.x-=v.x;this.y-=v.y;this.z-=v.z;return this;};
V3.prototype.add=function(v){this.x+=v.x;this.y+=v.y;this.z+=v.z;return this;};
V3.prototype.dot=function(v){return this.x*v.x+this.y*v.y+this.z*v.z;};
V3.prototype.length=function(){return Math.sqrt(this.dot(this));};
V3.prototype.normalize=function(){var l=this.length()||1;this.x/=l;this.y/=l;this.z/=l;return this;};
V3.prototype.multiplyScalar=function(s){this.x*=s;this.y*=s;this.z*=s;return this;};
V3.prototype.project=function(){return this;};
V3.prototype.applyMatrix4=function(){return this;};
V3.prototype.fromBufferAttribute=function(a,i){this.x=a.getX(i);this.y=a.getY(i);
  this.z=a.getZ(i);return this;};
function Obj(){this.children=[];this.position=new V3();this.rotation={x:0,y:0,z:0};
  this.scale=new V3(1,1,1);this.visible=true;this.userData={};
  this.matrixWorld={};this.renderOrder=0;this.frustumCulled=true;}
Obj.prototype.add=function(o){this.children.push(o);if(o)o.parent=this;return this;};
Obj.prototype.remove=function(o){var i=this.children.indexOf(o);if(i>=0)this.children.splice(i,1);if(o)o.parent=null;return this;};
Obj.prototype.localToWorld=function(v){return v;};
Obj.prototype.lookAt=function(){};
Obj.prototype.updateProjectionMatrix=function(){};
Obj.prototype.traverse=function(f){f(this);this.children.forEach(function(c){c.traverse&&c.traverse(f);});};
function Geo(){this.attributes={};}
Geo.prototype.setAttribute=function(k,v){this.attributes[k]=v;return this;};
Geo.prototype.dispose=function(){};
Geo.prototype.setIndex=function(){return this;};
Geo.prototype.computeBoundingSphere=function(){};
Geo.prototype.computeVertexNormals=function(){};
Geo.prototype.rotateX=function(){return this;};
Geo.prototype.rotateY=function(){return this;};
Geo.prototype.rotateZ=function(){return this;};
Geo.prototype.translate=function(){return this;};
Geo.prototype.scale=function(){return this;};
Geo.prototype.toNonIndexed=function(){return this;};
function Attr(arr,n){this.array=arr;this.itemSize=n;this.count=arr.length/n;
  this.needsUpdate=false;}
Attr.prototype.getX=function(i){return this.array[i*this.itemSize];};
Attr.prototype.getY=function(i){return this.array[i*this.itemSize+1];};
Attr.prototype.getZ=function(i){return this.array[i*this.itemSize+2];};
Attr.prototype.setX=function(i,v){this.array[i*this.itemSize]=v;return this;};
Attr.prototype.setY=function(i,v){this.array[i*this.itemSize+1]=v;return this;};
Attr.prototype.setZ=function(i,v){this.array[i*this.itemSize+2]=v;return this;};
Attr.prototype.setXYZ=function(i,x,y,z){var o=i*this.itemSize;
  this.array[o]=x;this.array[o+1]=y;this.array[o+2]=z;return this;};
function SphereGeo(r,w,h){
  Geo.call(this);
  var n=((w||8)+1)*((h||6)+1);
  var arr=new Float32Array(n*3);
  for(var i=0;i<n;i++){arr[i*3]=1;arr[i*3+1]=0;arr[i*3+2]=0;}
  this.setAttribute('position', new Attr(arr,3));
  this.setAttribute('normal', new Attr(new Float32Array(n*3),3));
}
SphereGeo.prototype=Object.create(Geo.prototype);
SphereGeo.prototype.constructor=SphereGeo;
function Col(h){this.r=1;this.g=1;this.b=1;this.setHex(h);}
Col.prototype.setHex=function(h){if(typeof h==='number'){this.r=((h>>16)&255)/255;
  this.g=((h>>8)&255)/255;this.b=(h&255)/255;}return this;};
Col.prototype.set=function(){return this;};
Col.prototype.clone=function(){return new Col();};
function Mat(){this.uniforms={};this.needsUpdate=false;}
Mat.prototype.dispose=function(){};
function mk(){ return function(){ var o=new Obj();
  o.geometry=arguments[0] instanceof Geo?arguments[0]:new Geo();
  o.material=new Mat(); return o; }; }
var THREE={
  Vector3:V3, Color:Col, Group:Obj, Scene:Obj, Object3D:Obj,
  BufferGeometry:Geo, BufferAttribute:Attr, Float32BufferAttribute:Attr,
  Points:mk(), LineSegments:mk(), Line:mk(), Mesh:mk(), Sprite:mk(),
  ShaderMaterial:Mat, PointsMaterial:Mat, LineBasicMaterial:Mat,
  MeshBasicMaterial:Mat, MeshPhongMaterial:Mat, SpriteMaterial:Mat,
  SphereGeometry:SphereGeo, SphereBufferGeometry:SphereGeo, RingGeometry:Geo,
  BoxGeometry:Geo, CircleGeometry:Geo,
  PerspectiveCamera:function(){var o=new Obj();o.aspect=1;
    o.projectionMatrix={};o.matrixWorldInverse={};return o;},
  WebGLRenderer:function(){return {setSize:function(){},setPixelRatio:function(){},
    getPixelRatio:function(){return 1;}, render:function(){},
    domElement:{}, setClearColor:function(){}, setScissorTest:function(){},
    getSize:function(){return new V3(900,600,0);}, dispose:function(){},
    info:{render:{}}, capabilities:{isWebGL2:true},
    getContext:function(){return {};}};},
  AdditiveBlending:2, NormalBlending:1, DoubleSide:2, FrontSide:0, BackSide:1,
  MeshLambertMaterial:Mat, MeshStandardMaterial:Mat, RawShaderMaterial:Mat,
  AmbientLight:mk(), DirectionalLight:mk(), PointLight:mk(), HemisphereLight:mk(),
  Fog:function(){return {};}, FogExp2:function(){return {};},
  TextureLoader:function(){return {load:function(){return {};}};},
  CanvasTexture:function(){return {};}, Texture:function(){return {};},
  Raycaster:function(){return {setFromCamera:function(){},
    intersectObjects:function(){return [];},params:{Points:{}}};},
  WireframeGeometry:SphereGeo, IcosahedronGeometry:Geo, CylinderGeometry:Geo, TorusGeometry:Geo,
  PlaneGeometry:Geo, EdgesGeometry:Geo, TubeGeometry:Geo,
  CatmullRomCurve3:function(){return {getPoints:function(){return [];}};},
  Quaternion:function(){return {setFromAxisAngle:function(){return this;}};},
  Euler:function(){return {};}, Clock:function(){return {getDelta:function(){return 0.016;}};},
  Matrix4:function(){return {};}, Vector2:function(x,y){this.x=x||0;this.y=y||0;}
};
module.exports = THREE;
V3.prototype.distanceTo=function(v){var dx=this.x-v.x,dy=this.y-v.y,dz=this.z-v.z;
  return Math.sqrt(dx*dx+dy*dy+dz*dz);};
V3.prototype.lerp=function(v,a){this.x+=(v.x-this.x)*a;this.y+=(v.y-this.y)*a;
  this.z+=(v.z-this.z)*a;return this;};
V3.prototype.cross=function(v){var x=this.y*v.z-this.z*v.y,
  y=this.z*v.x-this.x*v.z,z=this.x*v.y-this.y*v.x;this.x=x;this.y=y;this.z=z;return this;};
V3.prototype.addScaledVector=function(v,s){this.x+=v.x*s;this.y+=v.y*s;this.z+=v.z*s;return this;};
V3.prototype.setLength=function(l){return this.normalize().multiplyScalar(l);};
module.exports = THREE;
