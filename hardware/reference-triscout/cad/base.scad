// OpenPatrol TriScout: parametric three-wheel prototype deck, CERN-OHL-P-2.0
// Two driven wheels plus a rear caster. PROVISIONAL, not fabrication certified.
$fn=48;
deck_t=6; body_r=185; rear_trim=-125; grid=20; hole=4.4;

module delta_deck() {
  linear_extrude(deck_t) hull() {
    translate([105,115]) circle(r=42);
    translate([105,-115]) circle(r=42);
    translate([-130,0]) circle(r=42);
  }
}
module payload_holes() {
  for(x=[-80:grid:100]) for(y=[-80:grid:80])
    if(sqrt(x*x+y*y)<145) translate([x,y,-1]) cylinder(h=deck_t+2,d=hole);
}
module drive_slot(y) {
  translate([100,y,-1]) cube([82,42,deck_t+2],center=true);
  for(x=[48,152]) for(dy=[-22,22])
    translate([x,y+dy,-1]) cylinder(h=deck_t+2,d=5.2);
}
difference() {
  delta_deck(); payload_holes(); drive_slot(112); drive_slot(-112);
  translate([-130,0,-1]) cylinder(h=deck_t+2,d=48);
  translate([0,0,-1]) cylinder(h=deck_t+2,d=44);
}
