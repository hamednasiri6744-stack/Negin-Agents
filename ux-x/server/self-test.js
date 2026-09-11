const ux=require("./index");
const research=require("./research-skills");

const schemas=ux.toolSchemas();
const names=schemas.map(x=>x.name);
const expectedFigma=[
  "figma_x_status","figma_x_capabilities","figma_x_auth_status","figma_x_file_get",
  "figma_x_nodes_get","figma_x_images_get","figma_x_bridge_status",
  "figma_x_checkpoint_create","figma_x_apply_operations","figma_x_operation_status","figma_x_rollback"
];
const expectedResearch=["ux_research_skill_catalog","ux_research_skill_get","ux_research_skill_resolve"];
const expectedUx=["ux_status","ux_project_scan","ux_project_manifest","ux_component_inventory","ux_design_system_audit","ux_audit","ux_runtime_preflight","ux_runtime_audit","ux_test_plan","ux_quality_gate","ux_change_spec","ux_safe_patch_plan","ux_kit_catalog","ux_kit_recommend"];

for(const n of [...expectedUx,...expectedFigma,...expectedResearch]){
  if(!names.includes(n)) throw new Error("missing_tool:"+n);
}
const st=ux.status();
if(st.tool_count!==schemas.length) throw new Error("tool_count_mismatch");
for(const id of ["dribbble","mobbin","behance"]){
  if(!research.get(id).skill) throw new Error("missing_skill:"+id);
}
console.log(JSON.stringify({
  ok:true,
  version:st.version,
  tool_count:st.tool_count,
  figma_tools:expectedFigma.length,
  research_tools:expectedResearch.length,
  research_skills:research.catalog().skills.map(x=>x.id)
},null,2));
