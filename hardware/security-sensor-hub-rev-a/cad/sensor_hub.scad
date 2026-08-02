// OpenPatrol Security Sensor Hub Rev A — CERN-OHL-P-2.0
$fn=48;
part="assembly"; // assembly, bottom, lid, din_plate, led_bezel
flat=false;
w=220; d=170; h=72; wall=3; r=10;
module rr(x,y,rad){offset(r=rad) square([x-2*rad,y-2*rad],center=true);}
module shell_bottom(){difference(){linear_extrude(h-wall) rr(w,d,r);translate([0,0,wall]) linear_extrude(h) rr(w-2*wall,d-2*wall,r-wall);for(x=[-w/2+18,w/2-18])for(y=[-d/2+18,d/2-18])translate([x,y,8])cylinder(h=h,d=4.4);for(x=[-55:22:55])translate([x,-d/2-2,24])rotate([90,0,0])cylinder(h=8,d=12);}}
module lid(){difference(){union(){linear_extrude(wall) rr(w,d,r);translate([0,0,-9])linear_extrude(9)difference(){rr(w-2*wall,d-2*wall,r-wall);rr(w-2*wall-3,d-2*wall-3,r-wall-1);}}for(x=[-w/2+18,w/2-18])for(y=[-d/2+18,d/2-18])translate([x,y,-12])cylinder(h=20,d=4.4);translate([58,0,-3])linear_extrude(8)rr(70,34,5);for(x=[-28:7:28])translate([x,48,-4])cylinder(h=10,d=3);}}
module din_plate(){difference(){linear_extrude(2)rr(190,140,6);for(x=[-82,82])for(y=[-57,57])translate([x,y,-1])cylinder(h=4,d=4.5);for(x=[-60:20:60])for(y=[-35,35])translate([x,y,-1])hull(){translate([-5,0,0])cylinder(h=4,d=3.6);translate([5,0,0])cylinder(h=4,d=3.6);}}}
module led_bezel(){difference(){cylinder(h=6,d=15);cylinder(h=8,d=8);}}
module assembly(){color("#33373B")shell_bottom();color("#E7E4DC")translate([0,0,h+6])lid();color("#B8BBC0")translate([0,0,12])din_plate();color("#2F8BFF")translate([-72,55,h+8])led_bezel();}
if(part=="bottom")shell_bottom();else if(part=="lid")lid();else if(part=="din_plate"){if(flat)projection(cut=true)din_plate();else din_plate();}else if(part=="led_bezel")led_bezel();else assembly();
