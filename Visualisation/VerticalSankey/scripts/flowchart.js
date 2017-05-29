var margin = {top: 110, right: 65, bottom: 50, left: 65},
            width = 1300 - margin.left - margin.right,
            height = 600 - margin.top - margin.bottom;
            
        var formatNumber = d3.format(",.0f"),
            format = function(d) { return formatNumber(d) + " Seeks"; },
            color = d3.scale.category20();

        var svg = d3.select("#chart").append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .attr("class", "graph-svg-component")
          .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        var padding = 0

        var blue = "#0057e7",
            green = "#008744";

        var sankey = d3.sankey()
            .nodeWidth(100)
            .nodePadding(padding)
            .size([width, height]);

        var path = sankey.link();

        let selected_nodes = new Set();

        var last_selected_node = 0;

        var video_path = "bio_7_4";
        // var video_path = "spc_4_2";

        d3.json("../d3/data/" + video_path + ".json", function(error, graph) {

          var nodeMap = {};
          graph.nodes.forEach(function(x) { nodeMap[x.name] = x;  x.name = x.name.split(" ")[1];});
          graph.links = graph.links.map(function(x) {
            return {
              source: nodeMap[x.source],
              target: nodeMap[x.target],
              value: x.value,
              text: x.value_text,
              color: x.color
            };
          });

          var nodeSize = (width - (graph.nodes.length/2-1)*padding) / graph.nodes.length*2
          var nodeNumber = graph.nodes.length/2
          var nodeHeight = nodeSize*9/16
          // console.log('node size',nodeSize)
          sankey.nodeWidth(nodeHeight)

          sankey
              .nodes(graph.nodes)
              .links(graph.links)
              .layout(0)
              .nodeSize(nodeSize);

          var link = svg.append("g").selectAll(".link")
              .data(graph.links)
            .enter().append("path")
              .attr("class", "link")
              .attr("d", path)
              .attr("id", function(d,i){
                d.id = i;
                return "link-"+i;
              })
              .style("stroke-width", function(d) { return Math.max(1, d.dy); })
              .style("stroke", function(d){return d.color;})
              .style('visibility','hidden')
              .sort(function(a, b) { return b.dy - a.dy; });

          var linktext_top_dummy = svg.append("g").selectAll(".link")
              .data(graph.links)
            .enter()
            .append("text").attr('class','linkTextDummy')
              .attr("x", function(d) {
                return d.source.x + d.sy  + d.dy/2; })
              .attr("y", function(d) { return d.source.y + sankey.nodeWidth() + 25; })
              .attr("dy", ".35em")
              .attr("text-anchor", "middle")
              .attr("font-size",25)
              .attr("id", function(d,i){
                d.id = i;
                return "link_top_dummy-"+i;
              })
              .style('visibility','hidden')
              .attr("transform", null)
              .text(function(d) {return d.text; })
              .style('fill','black');


          var linktext_bottom_dummy = svg.append("g").selectAll(".link")
              .data(graph.links)
            .enter()
            .append("text").attr('class','linkTextDummy')
              .attr("x", function(d) { 
                return parseInt(d.target.name)*nodeSize + nodeSize/2 + d.ty ; })
              .attr("y", function(d) { return d.target.y - 25; })
              .attr("dy", ".35em")
              .attr("text-anchor", "middle")
              .attr("font-size",25)
              .attr("id", function(d,i){
                d.id = i;
                return "link_bottom_dummy-"+i;
              })
              .style('visibility','hidden')
              .text(function(d) { return d.text; })
              .style('fill','black');
            
          var node = svg.append("g").selectAll(".node")
              .data(graph.nodes)
            .enter().append("g")
              .attr("class", "node")
              .attr("type", function(d) { return d.name.slice(0,6);})
              .attr("transform", function(d) {
                  return "translate(" + d.x + "," + d.y + ")"; 
              })
              .on("click",highlight_node_links)
              .on("mouseover", mouse_in_node)
              .on("mouseout", mouse_out_node)
              .call(d3.behavior.drag()
              .origin(function(d) { return d; }) );

          node.append("rect")
              .attr("height", sankey.nodeWidth())
              .attr("width", nodeSize)
              .style("fill", function(d){ return d.color})
              .style("fill-opacity", function(d) { return d.alpha;})
              .style("stroke", function(d) { return d3.rgb(d.color).darker(2); })
              .style("stroke-width",1)
            
          // Slide number
          node.append("text")
              .attr('class','nodetitle')
              .attr("x", nodeSize / 2)
              .attr("y", sankey.nodeWidth() / 2)
              .attr("dy", ".35em")
              .attr("text-anchor", "middle")
              .attr("font-size",25)
              .attr("fill","white")
              .text(function(d) {return d.name; })


          // extra information about the incoming/outgoing seeks
          var node_infos = svg.append("g").selectAll(".node")
              .data(graph.nodes)
              .enter()
              .append("text").attr('class','node_infos')
              .attr("text-anchor", "middle")
              .attr("x", function(d) { return parseInt(d.name)*nodeSize + nodeSize/2 })
              .attr("y", function(d) {
                if (d.class_type == 'source')
                  return -15 + d.y;
                else
                  return 22 + d.y + nodeHeight;
              })
              .attr("id", function(d,i){
                d.id = i;
                return "node_infos-"+i;
              })
              .attr("fill", function(d) { return d.color; })
              .attr("dy", ".35em")
              .attr("font-size",15)
              .attr("visibility", "hidden")
              .text(function(d) { 
                var connection_word = '',
                    type = '', sum = 0;
                if (d.class_type == 'source') {
                  connection_word = 'from'
                  type = 'sourceLinks'
                  sum = d.outgoing_links
                } else {
                  connection_word = 'to'
                  type = 'targetLinks'
                  sum = d.incoming_links
                }
                // var sum = 0;
                // d[type].forEach(function(link) {
                //   sum += parseInt(link.text);
                // })
                return sum + ' users navigated\n ' + connection_word + ' this slide.'; 
              })
              .style("font-weight", "bold")



          var snapshots_background = svg.append("g").selectAll(".node")
              .data(graph.nodes)
              .enter()
              .append("rect")
              .attr("x", function(d) { return d.x })
              .attr("y", function(d) { return d.y - nodeHeight - 10- 30 })
              .attr("height", sankey.nodeWidth() + 10)
              .attr("width", nodeSize)
              .style("fill", function(d){ //return "#0057e7";
                return "black"})
              .style("fill-opacity", function(d) { return 1;})
              .style("stroke", "black")
              .style("stroke-width",1)
              .style("visibility", function(d) {
                if (d.class_type == 'source')
                  return "visible"
                else
                  return "hidden"
              })
              .attr("id", function(d,i){
                d.id = i;
                return "snapshots_background-"+i;
              })


          var snapshots_images = svg.append("g").selectAll(".node")
              .data(graph.nodes)
              .enter()
              .append("image")
              .attr("xlink:href", function(d) {
                return "snapshots/" + video_path + "/slide_" + d.name + ".png";
              })
              .attr("x", function(d) { return d.x; })
              // .attr("y", function(d) {return -nodeHeight - 5 + 2.5 - 30; })
              // .attr("height", nodeHeight - 5)
              .attr("y", function(d) {return -nodeHeight - 5 - 30; })
              .attr("height", nodeHeight)
              .attr("width", nodeSize )
              .style("visibility", function(d) {
                if (d.class_type == 'source')
                  return "visible"
                else
                  return "hidden"
              })
              .style("stroke", "black")
              .style("stroke-width",1)
              .attr("id", function(d,i){
                d.id = i;
                return "snapshots_images-"+i;
              })


          //  var big_images_background = svg.append("g").selectAll(".node")
          //     .data(graph.nodes)
          //     .enter()
          //     .append("rect")
          //     .attr("x", function(d) { return width/2 - 260; })
          //     .attr("y", function(d) { return -412; })
          //     .attr("width", 520 )
          //     .attr("height", 304)
          //     .style("fill", function(d){ //return "#0057e7";
          //       return "black"})
          //     .style("fill-opacity", function(d) { return 1;})
          //     .style("stroke", "black")
          //     .style("stroke-width",1)
          //     .style("visibility", "hidden")
          //     .style("opacity", 0)
          //     .attr("id", function(d,i){
          //       d.id = i;
          //       return "big_images_background-"+i;
          //     })


          // var big_images = svg.append("g").selectAll(".node")
          //     .data(graph.nodes)
          //     .enter()
          //     .append("image")
          //     .attr("xlink:href", function(d) {
          //       return "snapshots/" + video_path + "/slide_" + d.name + ".png";
          //     })
          //     .attr("x", function(d) { return width/2 - 260; })
          //     .attr("y", function(d) { return -410; })
          //     .attr("width", 520 )
          //     .attr("height", 300)
          //     .style("visibility", function(d) {
          //       if (d.class_type == 'source')
          //         return "hidden"
          //       else
          //         return "hidden"
          //     })
          //     // .style("stroke", "black")
          //     // .style("stroke-width",1)
          //     .attr("id", function(d,i){
          //       d.id = i;
          //       return "big_images-"+i;
          //     })


          function moveToRightPlace() {
            d3.selectAll('g.node')  //here's how you get all the nodes
              .each(function(d) {
                d.rightPlace = parseInt(d.name)*nodeSize + parseInt(d.name)*padding
                d3.select(this).attr("transform", "translate(" + (d.x = d.rightPlace) + "," + d.y + ")");
            });
            sankey.relayout();
            link.attr("d", path);
            linktext_bottom_dummy.attr("x", function(d) { return parseInt(d.target.name)*nodeSize + d.ty + d.dy/2 ; })
            linktext_top_dummy.attr("x", function(d) { return parseInt(d.source.name)*nodeSize + d.sy + d.dy/2 ; })
            snapshots_background.attr("x", function(d) { return parseInt(d.name)*nodeSize; })
            snapshots_images.attr("x", function(d) { return parseInt(d.name)*nodeSize; })
          }

          moveToRightPlace()

          linktext_top_dummy.each(function(d) {
            var bbox = this.getBBox();
            svg.append("rect")
              .attr("x", bbox.x -5)
              .attr("y", bbox.y)
              .attr("width", bbox.width + 10)
              .attr("height", bbox.height)
              .style("fill", "#fff")
              .style("fill-opacity", "1")
              .style("stroke", "#000")
              .style("stroke-width", "1.5px")
              .style("visibility", "hidden")
              .attr("id", function(){
                return "link_top_frame-"+d.id;
              });
          })

          var linktext_top = svg.append("g").selectAll(".link")
              .data(graph.links)
            .enter()
            .append("text").attr('class','linkText')
              .attr("x", function(d) {
                return d.source.x + d.sy  + d.dy/2; })
              .attr("y", function(d) { return d.source.y + sankey.nodeWidth() + 25; })
              .attr("dy", ".35em")
              .attr("text-anchor", "middle")
              .attr("font-size",25)
              .attr("id", function(d,i){
                d.id = i;
                return "link_top-"+i;
              })
              .style('visibility','hidden')
              .attr("transform", null)
              .text(function(d) {return d.text; })
              .style('fill','black');

          linktext_bottom_dummy.each(function(d) {
            var bbox = this.getBBox();
            svg.append("rect")
              .attr("x", bbox.x -5)
              .attr("y", bbox.y)
              .attr("width", bbox.width + 10)
              .attr("height", bbox.height)
              .style("fill", "#fff")
              .style("fill-opacity", "1")
              .style("stroke", "#000")
              .style("stroke-width", "1.5px")
              .style("visibility", "hidden")
              .attr("id", function(){
                return "link_bottom_frame-"+d.id;
              });
          })

          var linktext_bottom = svg.append("g").selectAll(".link")
              .data(graph.links)
            .enter()
            .append("text").attr('class','linkTextDummy')
              .attr("x", function(d) {
                return d.target.x + d.ty + d.dy/2; })
              .attr("y", function(d) { return d.target.y - 25; })
              .attr("dy", ".35em")
              .attr("text-anchor", "middle")
              .attr("font-size",25)
              .attr("id", function(d,i){
                d.id = i;
                return "link_bottom-"+i;
              })
              .style('visibility','hidden')
              .text(function(d) { return d.text; })
              .style('fill','black');
                        
          function dragmove(d) {
            //d3.select(this).attr("transform", "translate(" + d.x + "," + (d.y = Math.max(0, Math.min(height - d.dy, d3.event.y))) + ")");
            d3.select(this).attr("transform", "translate(" + (d.x = Math.max(0, Math.min(width - d.dy, d3.event.x))) + "," + d.y + ")");
            sankey.relayout();
            link.attr("d", path);

         
          }

          function update_text_info(n) {
            document.getElementById("table_timestamp_start").innerHTML = n.timestamp_start;
            document.getElementById("table_timestamp_end").innerHTML = n.timestamp_end;
            document.getElementById("table_users_in").innerHTML = n.incoming_links; 
            document.getElementById("table_users_out").innerHTML = n.outgoing_links;
            document.getElementById("table_slide_number").innerHTML = n.id % nodeNumber;

            document.getElementById("highlight_progress_bar").style.background = n.color;
            // document.getElementById("highlight_progress_bar").style.opacity = n.alpha;
            document.getElementById("highlight_progress_bar").style.border = "solid 2px rgba(0,0,0,1)"




            // document.getElementById("highlight_progress_bar").innerHTML = "ASDFGHJK"

          }

          function update_top_elements(n) {

            update_text_info(n);

            document.getElementById("top_picture").src = "snapshots/bio_7_4/slide_" + zeroPad(n.id % nodeNumber,2) + ".png";
            document.getElementById("top_div_container").style.visibility = "visible"
            document.getElementById("progress_bar_container").style.visibility = "visible"
            document.getElementById("slide_information_container").style.visibility = "visible"

            document.getElementById("before_progress_bar").style.width = n.progress_before + "px"
            document.getElementById("highlight_progress_bar").style.width = n.progress_highlight + "px"
            document.getElementById("after_progress_bar").style.width = n.progress_after + "px"

            if (n.id % nodeNumber == 0) {
              document.getElementById("before_progress_bar").style.border = "0"
              document.getElementById("highlight_progress_bar").style.borderLeft = "2px solid black"
              document.getElementById("highlight_progress_bar").style.borderTopLeftRadius = "6px"
              document.getElementById("highlight_progress_bar").style.borderBottomLeftRadius = "6px"
            } else {
              document.getElementById("before_progress_bar").style.borderLeft = "2px solid black"
              document.getElementById("before_progress_bar").style.borderTop = "2px solid black"
              document.getElementById("before_progress_bar").style.borderBottom = "2px solid black"
              document.getElementById("highlight_progress_bar").style.borderLeft = "0"
              document.getElementById("highlight_progress_bar").style.borderTopLeftRadius = "0px"
              document.getElementById("highlight_progress_bar").style.borderBottomLeftRadius = "0px"
            }

            if (n.id % nodeNumber == nodeNumber-1) {
              document.getElementById("after_progress_bar").style.border = "0"
              document.getElementById("highlight_progress_bar").style.borderRight = "2px solid black"
              document.getElementById("highlight_progress_bar").style.borderTopRightRadius = "6px"
              document.getElementById("highlight_progress_bar").style.borderBottomRightRadius = "6px"
            } else {
              document.getElementById("after_progress_bar").style.borderRight = "2px solid black"
              document.getElementById("after_progress_bar").style.borderTop = "2px solid black"
              document.getElementById("after_progress_bar").style.borderBottom = "2px solid black"
              document.getElementById("highlight_progress_bar").style.borderRight = "0"
              document.getElementById("highlight_progress_bar").style.borderTopRightRadius = "0px"
              document.getElementById("highlight_progress_bar").style.borderBottomRightRadius = "0px"
            }

          }

          function mouse_in_node(n,i) {

            var remainingNodes=[],
                nextNodes=[];

            var stroke_opacity = n.alpha;
            var stroke_color = n.color;
            var visibility = 'visible';
            var node_stroke_width = 5;
            var image_opacity = 0;

            update_top_elements(n);


            // d3.select("#big_images-" + n.id % nodeNumber).style("visibility", "visible")
            // d3.select("#big_images_background-" + n.id % nodeNumber).style("visibility", "visible")

            d3.select(this).select("rect").style("stroke-width", node_stroke_width)
            //d3.select(this).select("text").style("visibility", visibility)
            d3.select("#node_infos-" + n.id).style("visibility", visibility)
            //d3.select("#snapshots_background-" + n.id).style("stroke-width", node_stroke_width)

            d3.selectAll(".node").each(function(current_node) {
              if ((current_node.id%nodeNumber != n.id%nodeNumber)  & !(selected_nodes.has(current_node.id)) & !(selected_nodes.has(current_node.id % nodeNumber)) ) {
                image_opacity = 0.2;
              } else {
                image_opacity = 1;
              }
              d3.select("#snapshots_images-" + current_node.id % nodeNumber).style("opacity", image_opacity)
            })


            var traverse = [{
                              linkType : "sourceLinks",
                              nodeType : "target"
                            },{
                              linkType : "targetLinks",
                              nodeType : "source"
                            }];

            traverse.forEach(function(step){
              var node_class = step.nodeType
              n[step.linkType].forEach(function(link) {
                remainingNodes.push(link[step.nodeType]);
                highlight_link(link.id, stroke_opacity, stroke_color, visibility, node_class);
              });

              while (remainingNodes.length) {
                nextNodes = [];
                remainingNodes.forEach(function(node) {
                  node[step.linkType].forEach(function(link) {
                    nextNodes.push(link[step.nodeType]);
                    highlight_link(link.id, stroke_opacity, stroke_color, visibility, node_class);
                  });
                });
                remainingNodes = nextNodes;
              }
            });
          }

          function mouse_out_node(node,i) {


            var partial_opacity = 0.2;
            var complete_visibility = 1;
            // console.log("sel. nodes " + selected_nodes.size, node.id)

            
            if (selected_nodes.size == 0) {
              d3.selectAll(".node").each(function(current_node) {
                d3.select("#snapshots_images-" + current_node.id).style("opacity", complete_visibility) 
              })

              // document.getElementById("top_picture").src = "snapshots/bio_7_4/slide_" + zeroPad(n.id % nodeNumber,2) + ".png";
              document.getElementById("top_div_container").style.visibility = "hidden"
              document.getElementById("progress_bar_container").style.visibility = "hidden"
              document.getElementById("slide_information_container").style.visibility = "hidden"
              // d3.select("#big_images-" + node.id % nodeNumber).style("visibility", "hidden")
              // d3.select("#big_images_background-" + node.id % nodeNumber).style("visibility", "hidden")

            } else if ( !(selected_nodes.has(node.id)) & !(selected_nodes.has(node.id % nodeNumber)) ){
              d3.select("#snapshots_images-" + node.id).style("opacity", partial_opacity)

              document.getElementById("top_picture").src = "snapshots/bio_7_4/slide_" + zeroPad(last_selected_node % nodeNumber,2) + ".png";
              document.getElementById("top_div_container").style.visibility = "visible"
              document.getElementById("progress_bar_container").style.visibility = "visible"
              document.getElementById("slide_information_container").style.visibility = "visible"

              // d3.select("#big_images-" + node.id % nodeNumber).style("visibility", "hidden")
              // d3.select("#big_images_background-" + node.id % nodeNumber).style("visibility", "hidden")

            } else {

              document.getElementById("top_picture").src = "snapshots/bio_7_4/slide_" + zeroPad(last_selected_node % nodeNumber,2) + ".png";
              document.getElementById("top_div_container").style.visibility = "visible"
              document.getElementById("progress_bar_container").style.visibility = "visible"
              document.getElementById("slide_information_container").style.visibility = "visible"
              
              // d3.select("#big_images-" + node.id % nodeNumber).style("visibility", "visible")
              // d3.select("#big_images_background-" + node.id % nodeNumber).style("visibility", "visible")

            }


            

            if( d3.select(this).attr("data-clicked") != "1"  ) {

              var remainingNodes=[],
                  nextNodes=[];

              var stroke_opacity = node.alpha;
              var stroke_color = node.color;
              var visibility = 'hidden';
              var node_stroke_width = 1;

              d3.select(this).select("rect").style("stroke-width", node_stroke_width)
              d3.select("#node_infos-" + node.id).style("visibility", visibility)
              var traverse = [{
                                linkType : "sourceLinks",
                                nodeType : "target"
                              },{
                                linkType : "targetLinks",
                                nodeType : "source"
                              }];

              traverse.forEach(function(step){
              var node_class = step.nodeType
                node[step.linkType].forEach(function(link) {
                  remainingNodes.push(link[step.nodeType]);
                  highlight_link(link.id, stroke_opacity, stroke_color, visibility, node_class);
                });

                while (remainingNodes.length) {
                  nextNodes = [];
                  remainingNodes.forEach(function(node) {
                    node[step.linkType].forEach(function(link) {
                      nextNodes.push(link[step.nodeType]);
                      highlight_link(link.id, stroke_opacity, stroke_color, visibility, node_class);
                    });
                  });
                  remainingNodes = nextNodes;
                }
              });
            }
          }

          function highlight_node_links(node,i){

            var remainingNodes=[],
                nextNodes=[];

            var stroke_opacity = 0;
            var stroke_color = "";
            var rect_color = "";
            var visibility = "";

            if( d3.select(this).attr("data-clicked") == "1" ){
              d3.select(this).attr("data-clicked","0");
              // console.log(node.id + " clicked -> not clicked")
              
              selected_nodes.delete(node.id)

              stroke_color = "#C0C0C0"
              stroke_opacity = 0.3;
              rect_color = node.color
              visibility = 'hidden'


              // d3.select("#big_images-" + node.id % nodeNumber).style("visibility", visibility)
              // d3.select("#big_images_background-" + node.id % nodeNumber).style("visibility", visibility)

            }else{
              d3.select(this).attr("data-clicked","1");
              // console.log(node.id + " not clicked -> clicked")

              selected_nodes.add(node.id)
              last_selected_node = node.id
              
              stroke_color = node.color
              stroke_opacity = node.alpha
              // rect_color = "#87CEEB"
              rect_color = "#000"
              visibility = 'visible'

              // d3.select("#big_images-" + node.id % nodeNumber).style("visibility", visibility)
              // d3.select("#big_images_background-" + node.id % nodeNumber).style("visibility", visibility)
            }

            var traverse = [{
                              linkType : "sourceLinks",
                              nodeType : "target"
                            },{
                              linkType : "targetLinks",
                              nodeType : "source"
                            }];

            traverse.forEach(function(step){
              var node_class = step.nodeType
              node[step.linkType].forEach(function(link) {
                remainingNodes.push(link[step.nodeType])
                highlight_link(link.id, stroke_opacity, stroke_color, visibility, node_class);
              });

              while (remainingNodes.length) {
                nextNodes = [];
                remainingNodes.forEach(function(node) {
                  node[step.linkType].forEach(function(link) {
                    nextNodes.push(link[step.nodeType]);
                    
                    highlight_link(link.id, stroke_opacity, stroke_color, visibility, node_class);
                  });
                });
                remainingNodes = nextNodes;
              }
            });
          }

          function highlight_link(id,opacity,color, visibility, node_class){
              d3.select("#link-"+id).style("stroke-opacity", opacity);
              d3.select("#link-"+id).style("stroke", color);
              d3.select("#link-"+id).style("visibility", visibility);
              if (node_class == "source") {
                d3.select("#link_top-"+id).style("visibility", visibility);
                d3.select("#link_top_frame-"+id).style("visibility", visibility);

              } else {
                d3.select("#link_bottom-"+id).style("visibility", visibility);
                d3.select("#link_bottom_frame-"+id).style("visibility", visibility);
              }
              
          }
        });

        function zeroPad(num, places) {
          var zero = places - num.toString().length + 1;
          return Array(+(zero > 0 && zero)).join("0") + num;
        }