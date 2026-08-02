// OpenPatrol TriScout Rev A — CERN-OHL-P-2.0
// Two driven wheels plus one industrial caster. Engineering release, physically unvalidated.
$fn=64;
part="assembly";           // assembly, lower_deck, upper_deck, motor_saddle, cover_top, cover_side, lidar_plate
flat=false;
material_t=3;
mount_hole=4.4;
wheel_d=100;
wheel_w=40;
track=300;
axle_x=100;
deck_gap=78;

module rounded_plate(x,y,t,r=18){ linear_extrude(t) offset(r=r) square([x-2*r,y-2*r],center=true); }
module slot(length=18,width=5,height=10){ hull(){ translate([-length/2+width/2,0,0]) cylinder(h=height,d=width); translate([length/2-width/2,0,0]) cylinder(h=height,d=width); } }
module delta_plate(t=material_t){ linear_extrude(t) hull(){ translate([115,120]) circle(r=42); translate([115,-120]) circle(r=42); translate([-150,0]) circle(r=46); } }
module payload_grid(xs=160,ys=100,pitch=20,h=10){ for(x=[-xs/2:pitch:xs/2]) for(y=[-ys/2:pitch:ys/2]) translate([x,y,-1]) cylinder(h=h,d=mount_hole); }
module lower_deck(){
  difference(){
    delta_plate(); payload_grid(160,100,20,material_t+2);
    // Two adjustable motor saddle stations.
    for(y=[-106,106]) for(x=[78,132]) translate([x,y,-1]) slot(22,5,material_t+2);
    // 75 mm caster swivel: common 4-hole 45x30 pattern plus center relief.
    translate([-142,0,-1]) cylinder(h=material_t+2,d=34);
    for(x=[-164,-120]) for(y=[-18,18]) translate([x,y,-1]) slot(12,5,material_t+2);
    // Battery straps and service opening.
    for(y=[-38,38]) translate([-10,y,-1]) slot(110,7,material_t+2);
    translate([15,0,-1]) rounded_plate(72,48,material_t+2,7);
    for(x=[-125,135]) for(y=[-95,95]) translate([x,y,-1]) cylinder(h=material_t+2,d=5.2);
    for(y=[-115,115]) translate([160,y,-1]) cylinder(h=material_t+2,d=5.2);
  }
}
module upper_deck(){
  difference(){
    rounded_plate(300,230,material_t,18); payload_grid(220,140,20,material_t+2);
    for(x=[-29,29]) for(y=[-24.5,24.5]) translate([x-35,y,-1]) cylinder(h=material_t+2,d=3);
    for(x=[-42,42]) for(y=[-31,31]) translate([x+80,y,-1]) slot(12,4.2,material_t+2);
    for(x=[-130,130]) for(y=[-90,90]) translate([x,y,-1]) cylinder(h=material_t+2,d=5.2);
    translate([0,-90,-1]) rounded_plate(64,20,material_t+2,5);
  }
}
module motor_saddle(){
  difference(){ union(){ cube([54,20,18],center=true); translate([0,0,9]) rotate([90,0,0]) cylinder(h=20,d=46,center=true); } translate([0,0,9]) rotate([90,0,0]) cylinder(h=24,d=38.4,center=true); for(x=[-22,22]) translate([x,0,-12]) cylinder(h=30,d=5.2); translate([0,0,18]) cube([5,24,20],center=true); }
}
module lidar_plate(){ difference(){ rounded_plate(120,120,4,12); payload_grid(80,80,20,6); cylinder(h=6,d=18,center=true); } }
module cover_top(){ difference(){ rounded_plate(340,255,2,30); payload_grid(120,80,20,4); for(x=[-120:15:120]) translate([x,0,-1]) slot(26,4,4); } }
module cover_side(){ difference(){ cube([330,2,112],center=true); for(x=[-120:30:120]) translate([x,0,12]) rotate([90,0,0]) slot(18,4,5); for(x=[-150,150]) for(z=[-43,43]) translate([x,0,z]) rotate([90,0,0]) cylinder(h=5,d=4.2); } }
module wheel(y){ translate([axle_x,y,50]) rotate([90,0,0]) cylinder(h=wheel_w,d=wheel_d,center=true); }
module assembly(){ color("silver") translate([0,0,50]) lower_deck(); color("gainsboro") translate([0,0,50+deck_gap]) upper_deck(); color("#222") wheel(-track/2); color("#222") wheel(track/2); color("#222") translate([-145,0,18]) sphere(d=60); color("white",.7) translate([0,0,188]) cover_top(); color("white",.55) for(y=[-124,124]) translate([0,y,127]) cover_side(); color("#333") translate([35,0,192]) lidar_plate(); }
module selected(){ if(part=="lower_deck") lower_deck(); else if(part=="upper_deck") upper_deck(); else if(part=="motor_saddle") motor_saddle(); else if(part=="cover_top") cover_top(); else if(part=="cover_side") cover_side(); else if(part=="lidar_plate") lidar_plate(); else assembly(); }
if(flat && (part=="lower_deck" || part=="upper_deck" || part=="cover_top" || part=="cover_side" || part=="lidar_plate")) projection(cut=true) selected(); else selected();
