var margin = {top: 110, right: 65, bottom: 50, left: 65},
            width = 1500 - margin.left - margin.right,
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
            .zoomed(false)
            .size([width, height]);

        var path = sankey.link();

        // Currently selected nodes
        let selected_nodes = new Set();

        // Last selected node (to determine which slide is displayed on top)
        var last_selected_node = 0;

        // Path of the folder containing the snapshots, and name of the video
        var video_path = "bio-465_week7_part4";

        // Creation of the Sankey graph
        d3.json("data/json/" + video_path + ".json", function(error, graph) {

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

          // Measurements of the nodes, and different elements of the graphical display
          var nodeSize = (width - (graph.nodes.length/2-1)*padding) / graph.nodes.length*2
          var nodeNumber = graph.nodes.length/2
          var nodeHeight = nodeSize*9/16
          var target_y_zoomed = height - nodeHeight
          var padding_flowchart = 60

          // Application of the new dimensions to the graph
          sankey
              .nodeWidth(nodeHeight)
              .target_y(target_y_zoomed)
              .nodes(graph.nodes)
              .links(graph.links)
              .layout(0)
              .nodeSize(nodeSize);

          // Links between source and target nodes
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

          // The two following variables are made only for the construction of the final 
          // graph. They are not displayed.
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

          // Used only for construction
          var linktext_bottom_dummy = svg.append("g").selectAll(".link")
              .data(graph.links)
            .enter()
            .append("text").attr('class','linkTextDummy')
              .attr("x", function(d) { 
                return parseInt(d.target.name)*nodeSize + nodeSize/2 + d.ty ; })
              .attr("y", function(d) { return sankey.target_y() - 25; })
              .attr("dy", ".35em")
              .attr("text-anchor", "middle")
              .attr("font-size",25)
              .attr("id", function(d,i){
                d.id = i;
                return "link_bottom_dummy-"+i;
              })
              .style('visibility','hidden')
              .text(function(d) { return d.text; })
              .style('fill','red');
          
          // Creation of the nodes
          var node = svg.append("g").selectAll(".node")
              .data(graph.nodes)
            .enter().append("g")
              .attr("class", "node")
              .attr("type", function(d) { return d.name.slice(0,6);})
              .attr("transform", function(d) {
                  return "translate(" + d.x + "," + 0 + ")"; 
              })
              .on("click",highlight_node_links)
              .on("mouseover", mouse_in_node)
              .on("mouseout", mouse_out_node)
              .call(d3.behavior.drag()
              .origin(function(d) { return d; }) );

          // Creation of the rectangles around the nodes
          node.append("rect")
              .attr("height", sankey.nodeWidth())
              .attr("width", nodeSize)
              .style("fill", function(d){ return d.color})
              .style("fill-opacity", function(d) { return d.alpha;})
              .style("stroke", function(d) { return d3.rgb(d.color).darker(2); })
              .style("stroke-width",1)
            
          // Creation of the label containg the slide number, in the middle of the node
          node.append("text")
              .attr('class','nodetitle')
              .attr("x", nodeSize / 2)
              .attr("y", sankey.nodeWidth() / 2)
              .attr("dy", ".35em")
              .attr("text-anchor", "middle")
              .attr("font-size",25)
              .attr("fill","white")
              .text(function(d) {return d.name; })


          // Creation of the labels containing extra information about the nodes,
          // places above the source nodes and below the target ones.
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
                  return 22 + padding_flowchart + 2*nodeHeight;
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
                return sum + ' users navigated\n ' + connection_word + ' this slide.'; 
              })
              .style("font-weight", "bold")

          // Creation of the bar containing the snapshots of all the slides, above the
          // graph. These are the black backgrounds behind the actual snaphots.
          var snapshots_background = svg.append("g").selectAll(".node")
              .data(graph.nodes)
              .enter()
              .append("rect")
              .attr("x", function(d) { return d.x })
              .attr("y", function(d) { return d.y - nodeHeight - 10- 30 })
              .attr("height", sankey.nodeWidth() + 10)
              .attr("width", nodeSize)
              .style("fill", function(d){ 
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

          // Creation of the actual snapshots above the Sankey graph.
          var snapshots_images = svg.append("g").selectAll(".node")
              .data(graph.nodes)
              .enter()
              .append("image")
              .attr("xlink:href", function(d) {
                return "snapshots/" + video_path + "/slide_" + d.name + ".png";
              })
              .attr("x", function(d) { return d.x; })
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

          // Creation of the white background behind the graph
          svg.append("rect")
            .attr("class", "bg_rect")
            .attr("width", width)
            .attr("height", 2*nodeHeight + padding_flowchart)
            .attr("fill", "white")
            
          // Creation of the rectangle serving as button to expand the graph
          var flowchart_rect = svg.append("rect")
              .attr("class", "switch_rect")
              .attr("x", width/2 - 100)
              .attr("y", nodeHeight + 10)
              .attr("width", 200)
              .attr("height", padding_flowchart-20)
              .attr("fill", "#fafafa")
              .style("stroke", "black")
              .style("stroke-width", 1)
              .style("opacity", 0.3)
              .on("click", function() { first_expansion(true); })

          // Creation of the label of the button for the graph expansion
          var flowchart_text = svg.append("text")
              .attr("class", "switch_text")
              .attr("x",  width/2)
              .attr("y", nodeHeight + padding_flowchart/2)
              .attr("dy", ".35em")
              .attr("text-anchor", "middle")
              .attr("font-size",22)
              .attr("fill","black")
              .text("Expand Flowchart")


          // Relocation of all the elements, to make all the nodes equally spaced.
          function moveToRightPlace() {
            d3.selectAll('g.node')
              .each(function(d) {
                d.rightPlace = parseInt(d.name)*nodeSize + parseInt(d.name)*padding
                d3.select(this).attr("transform", function(d) { 
                   if (d.class_type == 'source') {
                    return "translate(" + (d.x = d.rightPlace) + "," + (d.y = 0) + ")";
                  } else {
                    return "translate(" + (d.x = d.rightPlace) + "," + (d.y = nodeHeight + padding_flowchart) + ")";
                  }
                })
                d3.select(this).attr("opacity", 1)
                if (d.class_type == 'target') d3.select(this).moveToBack()
            });

            // once the nodes are in the correct spot, we move the other elements
            sankey.relayout();
            link.attr("d", path);
            linktext_bottom_dummy.attr("x", function(d) { return parseInt(d.target.name)*nodeSize + d.ty + d.dy/2 ; })
            linktext_top_dummy.attr("x", function(d) { return parseInt(d.source.name)*nodeSize + d.sy + d.dy/2 ; })
            snapshots_background.attr("x", function(d) { return parseInt(d.name)*nodeSize; })
            snapshots_images.attr("x", function(d) { return parseInt(d.name)*nodeSize; })

            d3.selectAll(".switch_text").each(function(d) {d3.select(this).moveToBack()})
            d3.selectAll(".bg_rect").each(function(d) {d3.select(this).moveToBack()})

            // Initailization of the sliders and top element
            document.getElementById("top_video").style.zIndex = "1";
            document.getElementById("top_picture").style.zIndex = "2";

            document.getElementById("checkbox1").checked = false;
            document.getElementById("checkbox2").checked = false;
          }

          moveToRightPlace()

          // Update of the dummy top text elements (in order to create the real ones)
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
              .style("visibility", "hidden") // we hide them
              .attr("id", function(){
                return "link_top_frame-"+d.id;
              });
          })

          // Creation of the real top text elements
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

          // Update of the dummy bottom text elements (in order to create the real ones)
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
              .style("visibility", "hidden") // we hide them
              .attr("id", function(){
                return "link_bottom_frame-"+d.id;
              });
          })

          // Creation of the real bottom text elements
          var linktext_bottom = svg.append("g").selectAll(".link")
              .data(graph.links)
            .enter()
            .append("text").attr('class','linkTextDummy')
              .attr("x", function(d) {
                return d.target.x + d.ty + d.dy/2; })
              .attr("y", function(d) { return sankey.target_y() - 25; })
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

          // Update of all the elements of the top panel. The three elements of the progress
          // bar are scaled according to the currently selected node, as well as the picture
          // displayed.
          function update_top_elements(n) {

            // Settings for the highlighted part of the progress bar.
            document.getElementById("highlight_progress_bar").style.background = n.color;
            document.getElementById("highlight_progress_bar").style.border = "solid 2px rgba(0,0,0,1)"

            document.getElementById("top_picture").src = "snapshots/"+ video_path + "/slide_" + zeroPad(n.id % nodeNumber,2) + ".png";

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

          // Animation of the expansion / contraction of the Sankey graph.
          function update(nodeData, linkData, zoomed) {

            // Contraction
            if (zoomed == true) {
              node_infos.transition()
                .duration(1500)
                .attr("transform", function(d) {
                  if (d.class_type == 'source') {
                    return "translate(" + 0 + "," +  0 + ")";
                  } else {
                    return "translate(" + 0 + "," +  (target_y_zoomed - padding_flowchart - nodeHeight) + ")";
                  }
                })

              node.transition()
                .duration(1500)
                .attr("transform", function(d) {
                  if (d.class_type == 'source') {
                    return "translate(" + parseInt(d.name)*nodeSize  + "," +  0 + ")";
                  } else {
                    return "translate(" + d.x + "," + target_y_zoomed + ")";
                  }
                })
                .each('end', function() { 
                  sankey.zoomed(true)
                })

              d3.selectAll(".bg_rect").transition()
                .duration(1500)
                .attr("height", height)
                .each("end", function() {
                  d3.selectAll(".node").each(function(current_node) {
                  if (selected_nodes.has(current_node.id)) {
                    var remainingNodes=[],
                      nextNodes=[];

                    var stroke_opacity = current_node.alpha;
                    var stroke_color = current_node.color;
                    var visibility = 'visible';
                    var node_stroke_width = 1;

                    var traverse = [{
                                      linkType : "sourceLinks",
                                      nodeType : "target"
                                    },{
                                      linkType : "targetLinks",
                                      nodeType : "source"
                                    }];

                    traverse.forEach(function(step){
                    var node_class = step.nodeType
                      current_node[step.linkType].forEach(function(link) {
                        remainingNodes.push(link[step.nodeType]);
                        highlight_link(link.id, stroke_opacity, stroke_color, visibility, node_class);
                      });
                    });
                  }
                })
                })

            // Expansion
            } else {

              d3.selectAll(".link").each(function(d) {
                d3.select("#link-"+d.id).style("visibility", "hidden");
                d3.select("#link_top-"+d.id).style("visibility", "hidden");
                d3.select("#link_top_frame-"+d.id).style("visibility", "hidden");
                d3.select("#link_bottom-"+d.id).style("visibility", "hidden");
                d3.select("#link_bottom_frame-"+d.id).style("visibility", "hidden");
              })

              node_infos.transition()
                .duration(1500)
                .attr("transform", function(d) {
                  if (d.class_type == 'source') {
                    return "translate(" + 0 + "," +  0 + ")";
                  } else {
                    return "translate(" + 0 + "," +  0 + ")";
                  }
                })

              node.transition()
                .duration(1500)
                .attr("transform", function(d) {
                  if (d.class_type == 'source') {
                    return "translate(" + parseInt(d.name)*nodeSize  + "," +  0 + ")";
                  } else {
                    return "translate(" + d.x + "," + (nodeHeight + padding_flowchart) + ")";
                  }
                })
                .each('start', function() {
                  sankey.zoomed(false)
                })

              d3.selectAll(".bg_rect").transition()
                .duration(1500)
                .attr("height", 2*nodeHeight + padding_flowchart)
            }       

            sankey.relayout();
          };

          // When the user puts his mouse over a node
          function mouse_in_node(n,i) {

            var remainingNodes=[],
                nextNodes=[];

            var stroke_opacity = n.alpha;
            var stroke_color = n.color;
            var visibility = 'visible';
            var node_stroke_width = 5;
            var image_opacity = 0;

            d3.select(this).select("rect").style("stroke-width", node_stroke_width)

            // Update the opacity of the snapshots bar
            for (i = 0; i < nodeNumber; i++) {
              if ( (i != n.id % nodeNumber) & !(selected_nodes.has(i)) & !(selected_nodes.has(i + nodeNumber))) {
                image_opacity = 0.2;
              } else {
                image_opacity = 1;
              }
              d3.select("#snapshots_images-" + i).style("opacity", image_opacity)
            }

            d3.select("#node_infos-" + n.id).style("visibility", visibility)

            update_top_elements(n);

            // Update of the video, if the slider is checked
            if (document.querySelector("input[name=checkbox2]").checked == true) {
              var top_vid = document.getElementById("top_video")

              top_vid.play();
              top_vid.pause();
              top_vid.currentTime = n.starting_time;
              top_vid.play();
            }

            // If the graph is expanded
            if (sankey.zoomed()) {

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
          }

          // When the user gets his mouse out of a node
          function mouse_out_node(node,i) {

            var partial_opacity = 0.2;
            var complete_visibility = 1;

            // If there is no selected node
            if (selected_nodes.size == 0) {
              d3.selectAll(".node").each(function(current_node) {
                d3.select("#snapshots_images-" + current_node.id).style("opacity", complete_visibility) 
              })

              document.getElementById("before_progress_bar").style.width = 320 + "px"
              document.getElementById("highlight_progress_bar").style.width = 0 + "px"
              document.getElementById("after_progress_bar").style.width = 320 + "px"
              document.getElementById("before_progress_bar").style.borderLeft = "2px solid black"
              document.getElementById("before_progress_bar").style.borderTop = "2px solid black"
              document.getElementById("before_progress_bar").style.borderBottom = "2px solid black"
              document.getElementById("highlight_progress_bar").style.border = "0"
              document.getElementById("highlight_progress_bar").style.borderTopRightRadius = "0px"
              document.getElementById("highlight_progress_bar").style.borderBottomRightRadius = "0px"
              document.getElementById("after_progress_bar").style.borderRight = "2px solid black"
              document.getElementById("after_progress_bar").style.borderTop = "2px solid black"
              document.getElementById("after_progress_bar").style.borderBottom = "2px solid black"

              document.getElementById("top_picture").src = "snapshots/"+ video_path + "/slide_00.png";

            } else {
              var current_displayed_node = 0
              if (selected_nodes.size == 1) {
                current_displayed_node =  selected_nodes.values().next().value
              } else {
                document.getElementById("before_progress_bar").style.width = 320 + "px"
                document.getElementById("highlight_progress_bar").style.width = 0 + "px"
                document.getElementById("after_progress_bar").style.width = 320 + "px"
                document.getElementById("before_progress_bar").style.borderLeft = "2px solid black"
                document.getElementById("before_progress_bar").style.borderTop = "2px solid black"
                document.getElementById("before_progress_bar").style.borderBottom = "2px solid black"
                document.getElementById("highlight_progress_bar").style.border = "0"
                document.getElementById("highlight_progress_bar").style.borderTopRightRadius = "0px"
                document.getElementById("highlight_progress_bar").style.borderBottomRightRadius = "0px"
                document.getElementById("after_progress_bar").style.borderRight = "2px solid black"
                document.getElementById("after_progress_bar").style.borderTop = "2px solid black"
                document.getElementById("after_progress_bar").style.borderBottom = "2px solid black"

                current_displayed_node = 0;
              }
              document.getElementById("top_picture").src = "snapshots/bio-465_week7_part4/slide_" + zeroPad(current_displayed_node % nodeNumber,2) + ".png";

              for (i = 0; i < nodeNumber; i++) {
                if ( !(selected_nodes.has(i)) & !(selected_nodes.has(i + nodeNumber))) {
                  image_opacity = 0.2;
                } else {
                  image_opacity = 1;
                }
                d3.select("#snapshots_images-" + i).style("opacity", image_opacity)
              }
            }

            // When the node is not selected, get all the elements back to normal
            if( d3.select(this).attr("data-clicked") != "1"  ) {

              var remainingNodes=[],
                  nextNodes=[];

              var stroke_opacity = node.alpha;
              var stroke_color = node.color;
              var visibility = 'hidden';
              var node_stroke_width = 1;

              d3.select(this).select("rect").style("stroke-width", node_stroke_width)

              d3.select("#node_infos-" + node.id).style("visibility", visibility)

              // Only if the graph is expanded
              if (sankey.zoomed()) {

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
                        highlight_link(link.id, stroke_opacity, stroke_color, visibility, "source");
                      });
                    });
                    remainingNodes = nextNodes;
                  }
                });
              }
            }
          }

          // When the user clicks on a node
          function highlight_node_links(node,i){

            var remainingNodes=[],
                nextNodes=[];

            var stroke_opacity = 0;
            var stroke_color = "";
            var rect_color = "";
            var visibility = "";

            if( d3.select(this).attr("data-clicked") == "1" ){

              // Update of the set of selected nodes, as well as the state of the node itself
              d3.select(this).attr("data-clicked","0");              
              selected_nodes.delete(node.id)

              // Set the parameters for the links
              stroke_color = "#C0C0C0"
              stroke_opacity = 0.3;
              rect_color = node.color
              visibility = 'hidden'

            } else {

              d3.select(this).attr("data-clicked","1");
              selected_nodes.add(node.id)
              last_selected_node = node.id
              
              stroke_color = node.color
              stroke_opacity = node.alpha
              rect_color = "#000"
              visibility = 'visible'
            }

            // Only if the graph is expanded
            if (sankey.zoomed()) {

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
          }

          // Set the correct thickness and visibility for the node
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

          // VIDEO PART

          // slider for switching between picture and video display
          var slider_zoom = document.getElementById('checkbox1');

          slider_zoom.onclick = function(){
              first_expansion(slider_zoom.checked)
          }

          var checkbox_video = document.querySelector("input[name=checkbox2]");
          var top_vid = document.getElementById("top_video")
          var top_pict = document.getElementById("top_picture")

          checkbox_video.onchange = function() {
          if(this.checked) {
              document.getElementById("top_video").style.zIndex = "2";
              document.getElementById("top_picture").style.zIndex = "1";

              document.getElementById("elapsed_time_span").style.visibility = "visible"
              document.getElementById("remaining_time_span").style.visibility = "visible"

              // document.getElementById("top_video").addEventListener("loadedmetadata", function() {
              //   this.play();
              // }, false);

              top_vid.play();
            } else {
              document.getElementById("top_video").style.zIndex = "1";
              document.getElementById("top_picture").style.zIndex = "2";

              document.getElementById("elapsed_time_span").style.visibility = "hidden"
              document.getElementById("remaining_time_span").style.visibility = "hidden"

              document.getElementById("top_video").pause()  
            }
          }

          document.getElementById("top_video").ontimeupdate = function() {
            onTrackedVideoFrame(this.currentTime, this.duration);
          }

          // Update of the two time elements around the progress bar
          function onTrackedVideoFrame(currentTime, duration){
              document.getElementById("elapsed_time_span").innerHTML = seconds_to_fancy(currentTime, true);
              document.getElementById("remaining_time_span").innerHTML = seconds_to_fancy(duration - currentTime, false);
          }

          // Expansion
          function first_expansion(bool_checked) {

              update(graph.nodes, graph.links, bool_checked)

              // Animation of the button inside the graph.
              if (bool_checked == true) {
                flowchart_rect.transition().duration(1500).style("opacity",0).each('end', function(d) {d3.select(this).moveToBack()})
                flowchart_text.transition().duration(1500).style("opacity",0).each('end', function(d) {d3.select(this).moveToBack()})
              } else {
                flowchart_text.transition().duration(1500).style("opacity",1).each('start', function(d) {d3.select(this).moveToFront()})
                flowchart_rect.transition().duration(1500).style("opacity",0.3).each('start', function(d) {d3.select(this).moveToFront()})
              }
              document.getElementById("checkbox1").checked = bool_checked;
          }

        });

        // UTILITIES

        // Padding to match correct name of file
        function zeroPad(num, places) {
          var zero = places - num.toString().length + 1;
          return Array(+(zero > 0 && zero)).join("0") + num;
        }

        // Add zeros to a int (to match a standard)
        function pad(num, size) {
          return ('000000000' + num).substr(-size);
        }

        // Transforms the amount of seconds into a correct min:sec expression
        function seconds_to_fancy(timestamp, bool_elapsed) {
          var seconds = Math.round(timestamp);
          var floatingPointPart = Math.round(((seconds/60) % 1)*60);
          var integerPart = Math.floor(seconds/60);
          if (bool_elapsed==true) {
            return pad(integerPart,2) + ':' + pad(floatingPointPart,2)
          } else {
            return '- ' + pad(integerPart,2) + ':' + pad(floatingPointPart,2)
          }
        }

        // Functions used for z-index management

        d3.selection.prototype.moveToFront = function() {  
          return this.each(function(){
            this.parentNode.appendChild(this);
          });
        };

        d3.selection.prototype.moveToBack = function() {  
            return this.each(function() { 
                var firstChild = this.parentNode.firstChild; 
                if (firstChild) { 
                    this.parentNode.insertBefore(this, firstChild); 
                } 
            });
        };
