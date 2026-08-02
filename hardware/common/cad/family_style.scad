// OpenPatrol plain-future visual language — CERN-OHL-P-2.0
// Shared appearance modules. Structural/fabrication dimensions remain in each platform file.
$fn=48;
OP_SHELL="#E7E4DC";
OP_DARK="#25282B";
OP_GLASS="#111418";
OP_BLUE="#2F8BFF";
OP_AMBER="#FFB343";
OP_WHITE="#F2F7FF";

module op_round_box(size=[100,80,40],r=10,center=true){
  x=size[0]; y=size[1]; z=size[2];
  translate(center?[0,0,0]:[x/2,y/2,z/2])
    hull() for(ix=[-1,1]) for(iy=[-1,1]) for(iz=[-1,1])
      translate([ix*(x/2-r),iy*(y/2-r),iz*(z/2-r)]) sphere(r=r);
}

module op_ground_shell(length=390,width=275,height=105,nose_taper=32,roof_drop=10){
  color(OP_SHELL)
  hull(){
    translate([-length*.18,0,height*.54]) op_round_box([length*.62,width*.94,height*.82],r=24);
    translate([ length*.28,0,height*.42]) op_round_box([length*.28,width*.82,height*.55],r=18);
  }
  // Charcoal lower belt gives every product the same visual datum.
  color(OP_DARK) translate([0,0,height*.16]) op_round_box([length*.94,width,height*.31],r=18);
}

module op_wheel(d=100,w=40){
  color("#161719") rotate([90,0,0]) cylinder(h=w,d=d,center=true);
  color("#303236") rotate([90,0,0]) cylinder(h=w+1,d=d*.54,center=true);
}
module op_lidar(d=72,h=38){
  color(OP_GLASS) cylinder(h=h,d=d,center=false);
  color(OP_BLUE) translate([0,0,h*.42]) difference(){cylinder(h=3,d=d+2);cylinder(h=4,d=d-2);}
  color(OP_SHELL) translate([0,0,h]) cylinder(h=5,d=d*.94);
}
module op_antenna(h=95,d=5){
  color(OP_DARK) cylinder(h=h*.78,d=d);
  color(OP_DARK) translate([0,0,h*.78]) cylinder(h=h*.22,d1=d,d2=1.5);
}
module op_led_bar(length=54,height=7,depth=3,color_value=OP_WHITE){
  color(color_value) op_round_box([length,depth,height],r=min(3,height/2));
}
module op_camera_bar(width=95,height=32,depth=18){
  color(OP_GLASS) op_round_box([depth,width,height],r=7);
  for(y=[-width*.26,width*.26]) color("#25384D") translate([-depth*.52,y,0]) rotate([0,90,0]) cylinder(h=2,d=12);
}
module op_masked_head(size=[190,110,85]){
  color(OP_SHELL) op_round_box(size,r=16);
  color(OP_GLASS) translate([-size[0]/2-1,0,0]) op_round_box([4,size[1]*.78,size[2]*.62],r=9);
  for(y=[-size[1]*.22,0,size[1]*.22]) color("#1E3044")
    translate([-size[0]/2-4,y,0]) rotate([0,90,0]) cylinder(h=3,d=14);
  color(OP_BLUE) translate([-size[0]/2-6,size[1]*.32,-size[2]*.18]) rotate([0,90,0]) cylinder(h=3,d=5);
}
module op_telescoping_mast(retracted=360,travel=520,extension=1,sections=3){
  e=max(0,min(1,extension));
  base_h=retracted*.42;
  color(OP_DARK) cylinder(h=base_h,d=82);
  color("#30343A") translate([0,0,base_h*.72]) cylinder(h=retracted*.38+travel*e*.42,d=65);
  color("#3C4148") translate([0,0,base_h+travel*e*.34]) cylinder(h=retracted*.28+travel*e*.58,d=49);
}
module op_drone_shell(length=210,width=145,height=76){
  color(OP_SHELL) hull(){
    translate([-length*.15,0,0]) op_round_box([length*.62,width,height],r=18);
    translate([ length*.28,0,-height*.08]) op_round_box([length*.26,width*.72,height*.58],r=14);
  }
  color(OP_DARK) translate([length*.38,0,-height*.20]) op_round_box([42,76,36],r=9);
}
