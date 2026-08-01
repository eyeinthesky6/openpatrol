// OpenPatrol Rover One: parametric 4WD prototype deck, CERN-OHL-P-2.0
// PROVISIONAL: verify motor, bearing and enclosure dimensions before cutting.
$fn=48;
deck_x=420; deck_y=320; deck_t=6; corner_r=22;
payload_grid=20; payload_hole=4.4; axle_x=145;
motor_slot_x=70; motor_slot_y=36; motor_hole=5.2;

module rounded_deck() {
  linear_extrude(deck_t) offset(r=corner_r)
    square([deck_x-2*corner_r,deck_y-2*corner_r],center=true);
}
module payload_holes() {
  for(x=[-100:payload_grid:100]) for(y=[-80:payload_grid:80])
    translate([x,y,-1]) cylinder(h=deck_t+2,d=payload_hole);
}
module motor_mount(x,y) {
  translate([x,y,-1]) {
    cube([motor_slot_x,motor_slot_y,deck_t+2],center=true);
    for(dx=[-motor_slot_x/2-8,motor_slot_x/2+8])
      for(dy=[-18,18]) translate([dx,dy,0]) cylinder(h=deck_t+2,d=motor_hole);
  }
}
module service_cuts() {
  translate([0,0,-1]) cube([105,70,deck_t+2],center=true);
  for(x=[-165,165]) translate([x,0,-1]) cube([28,150,deck_t+2],center=true);
}
difference() {
  rounded_deck(); payload_holes(); service_cuts();
  for(x=[-axle_x,axle_x]) for(y=[-deck_y/2+38,deck_y/2-38]) motor_mount(x,y);
}
