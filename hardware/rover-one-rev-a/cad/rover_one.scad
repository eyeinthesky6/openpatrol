// OpenPatrol Rover One Rev A — CERN-OHL-P-2.0
// Engineering release. Fabrication dimensions are complete; physical validation is not.
$fn = 64;
part = "assembly";          // assembly, lower_deck, upper_deck, motor_saddle, cover_top, cover_side, lidar_plate, camera_bracket
flat = false;               // true for DXF projection of sheet parts
material_t = 3;
plate_x = 420;
plate_y = 300;
corner_r = 22;
wheel_d = 100;
wheel_w = 40;
wheelbase = 260;
track = 340;
deck_gap = 82;
mount_hole = 4.4;
slot_w = 5.0;

module rounded_plate(x, y, t, r=18) {
  linear_extrude(t) offset(r=r) square([x-2*r, y-2*r], center=true);
}
module slot(length=18, width=slot_w, height=10) {
  hull() {
    translate([-length/2+width/2,0,0]) cylinder(h=height,d=width);
    translate([ length/2-width/2,0,0]) cylinder(h=height,d=width);
  }
}
module payload_grid(xspan=160, yspan=100, pitch=20, h=10) {
  for (x=[-xspan/2:pitch:xspan/2]) for (y=[-yspan/2:pitch:yspan/2])
    translate([x,y,-1]) cylinder(h=h,d=mount_hole);
}
module lower_deck() {
  difference() {
    rounded_plate(plate_x, plate_y, material_t, corner_r);
    payload_grid(180,120,20,material_t+2);
    // Four adjustable motor-saddle stations for 37 mm/Johnson gearmotors.
    for (x=[-wheelbase/2,wheelbase/2]) for (y=[-112,112]) {
      translate([x-26,y,-1]) slot(22,slot_w,material_t+2);
      translate([x+26,y,-1]) slot(22,slot_w,material_t+2);
    }
    // Battery straps, cable glands, service and drain openings.
    for (y=[-45,45]) translate([0,y,-1]) slot(130,7,material_t+2);
    translate([0,0,-1]) rounded_plate(90,54,material_t+2,8);
    for (x=[-170,170]) translate([x,0,-1]) cylinder(h=material_t+2,d=24);
    // Upper deck standoffs and bumper pivots.
    for (x=[-170,170]) for (y=[-118,118]) translate([x,y,-1]) cylinder(h=material_t+2,d=5.2);
    for (x=[-190,190]) for (y=[-85,85]) translate([x,y,-1]) cylinder(h=material_t+2,d=5.2);
  }
}
module upper_deck() {
  difference() {
    rounded_plate(360,250,material_t,18);
    payload_grid(240,160,20,material_t+2);
    // Pi 5 58x49 pattern, M2.5 clearance.
    for (x=[-29,29]) for (y=[-24.5,24.5]) translate([x,y,-1]) cylinder(h=material_t+2,d=3.0);
    // Cytron MDD10A 84.5x62 envelope with slotted mounting.
    for (x=[-42,42]) for (y=[-31,31]) translate([x+105,y,-1]) slot(12,4.2,material_t+2);
    // Ventilation and harness pass-through.
    for (x=[-135:15:-75]) translate([x,0,-1]) slot(34,5,material_t+2);
    translate([0,-95,-1]) rounded_plate(70,22,material_t+2,6);
    for (x=[-150,150]) for (y=[-95,95]) translate([x,y,-1]) cylinder(h=material_t+2,d=5.2);
  }
}
module motor_saddle() {
  // Printable clamp for a 36–38 mm motor body; two saddles per motor.
  difference() {
    union() {
      cube([54,20,18],center=true);
      translate([0,0,9]) rotate([90,0,0]) cylinder(h=20,d=46,center=true);
    }
    translate([0,0,9]) rotate([90,0,0]) cylinder(h=24,d=38.4,center=true);
    for (x=[-22,22]) translate([x,0,-12]) cylinder(h=30,d=5.2);
    translate([0,0,18]) cube([5,24,20],center=true);
  }
}
module lidar_plate() {
  difference() {
    rounded_plate(120,120,4,12);
    payload_grid(80,80,20,6);
    cylinder(h=6,d=18,center=true);
  }
}
module camera_bracket() {
  difference() {
    union(){ cube([70,4,42],center=true); translate([0,-18,-19]) cube([70,36,4],center=true); }
    for(x=[-28,28]) translate([x,0,0]) slot(16,4,8);
    for(x=[-25,25]) translate([x,-18,-24]) cylinder(h=12,d=4.2);
  }
}
module cover_top() {
  difference(){ rounded_plate(390,275,2,28); payload_grid(160,80,20,4); for(x=[-150:15:150]) translate([x,0,-1]) slot(28,4,4); }
}
module cover_side() {
  difference(){ cube([390,2,122],center=true); for(x=[-150:30:150]) translate([x,0,15]) rotate([90,0,0]) slot(18,4,5); for(x=[-175,175]) for(z=[-48,48]) translate([x,0,z]) rotate([90,0,0]) cylinder(h=5,d=4.2); }
}
module wheel(x,y){ translate([x,y,0]) rotate([90,0,0]) cylinder(h=wheel_w,d=wheel_d,center=true); }
module assembly() {
  color("silver") translate([0,0,50]) lower_deck();
  color("gainsboro") translate([0,0,50+deck_gap]) upper_deck();
  for(x=[-wheelbase/2,wheelbase/2]) for(y=[-track/2,track/2]) color("#222") wheel(x,y,50);
  color("white",.7) translate([0,0,194]) cover_top();
  color("white",.55) for(y=[-144,144]) translate([0,y,133]) cover_side();
  color("#333") translate([65,0,198]) lidar_plate();
  color("#333") translate([205,0,145]) rotate([0,0,90]) camera_bracket();
}
module selected(){
  if(part=="lower_deck") lower_deck();
  else if(part=="upper_deck") upper_deck();
  else if(part=="motor_saddle") motor_saddle();
  else if(part=="cover_top") cover_top();
  else if(part=="cover_side") cover_side();
  else if(part=="lidar_plate") lidar_plate();
  else if(part=="camera_bracket") camera_bracket();
  else assembly();
}
if(flat && (part=="lower_deck" || part=="upper_deck" || part=="cover_top" || part=="cover_side" || part=="lidar_plate")) projection(cut=true) selected(); else selected();
