/**
 * This is a bridge between ultrafast particle renderer and react world.
 *
 * It listens to graph loading events. Once graph positions are loaded it calls
 * native renderer to show the positions.
 *
 * It also listens to native renderer for user interaction. When user hovers
 * over a node or clicks on it - it reports user actions back to the global
 * events bus. These events are later consumed by stores to show appropriate
 * UI feedback
 */

// TODO: This class needs to be refactored. It is doing too much, and parts
// of its code should be done from unrender itself
// TODO: Use DynamicBufferAttribute which can accelarate render
// E.g.: threejs.org/examples/webgl_buffergeometry_drawcalls.html
import unrender from 'unrender';
window.THREE = unrender.THREE;

import eventify from 'ngraph.events';
import appEvents from '../service/appEvents.js';
import scene from '../store/scene.js';
import getNearestIndex from './getNearestIndex.js';
import createTouchControl from './touchControl.js';
import createLineView from './lineView.js';
import appConfig from './appConfig.js';

export default sceneRenderer;

var nodeCommunity = [];
//var highlightNodeColor = 0xff0000ff;
var highlightNodeColor = 0x000080ff;


function sceneRenderer(container) {
  var renderer, positions, graphModel, touchControl;
  var hitTest, lastHighlight, lastHighlightSize, cameraPosition;
  var lineView, links, lineViewNeedsUpdate;
  var queryUpdateId = setInterval(updateQuery, 200);

  appEvents.positionsDownloaded.on(setPositions);
  appEvents.labelsDownloaded.on(setLabels);
  appEvents.linksDownloaded.on(setLinks);
  appEvents.toggleSteering.on(toggleSteering);
  appEvents.focusOnNode.on(focusOnNode);
  appEvents.around.on(around);
  appEvents.highlightQuery.on(highlightQuery);
  appEvents.highlightLinks.on(highlightLinks);
  appEvents.accelerateNavigation.on(accelarate);
  appEvents.focusScene.on(focusScene);
  appEvents.cls.on(cls);

  var communityColorMap = new Map();
//  var colorMap = {
//    0: 0x00f7ffff,
//    1: 0x1a14ffff,
//    2: 0x6e30ffff,
//    3: 0x1189ffff,
//    4: 0xde38ffff,
//    5: 0xfff10cff,
//    6: 0xff3254ff,
//    7: 0x4dea00ff
//};

//  var colorMap = new Map([
//    [0, 0x00f7ffff],// 青色
//    [1, 0x1a14ffff],// 蓝色
//    [2, 0x6e30ffff],// 蓝色
//    [3, 0x1189ffff],// 蓝色
//    [4, 0xde38ffff],// 紫色
//    [5, 0xfff10cff],// 黄色
//    [6, 0xff0000ff],// 粉红
//    [7, 0x4dea00ff],// 绿色
//  ]);


  var colorMap = new Map([
    [0, 0x00f7ffff],// 青色
    [1, 0x1a14ffff],// 蓝色
    [2, 0x6e30ffff],// 蓝色
    [3, 0x1189ffff],// 蓝色
    [4, 0xde38ffff],// 紫色
    [5, 0xfff10cff],// 黄色
    [6, 0xff3254ff],// 红色
    [7, 0x4dea00ff],// 绿色
  ]);

  var defaultNodeColor = 0xffffffff;
  //var defaultNodeColor = colorMap.get(7);


  appConfig.on('camera', moveCamera);
  appConfig.on('showLinks', toggleLinks);

  var api = {
    destroy: destroy
  };

  eventify(api);

  return api;

  function accelarate(isPrecise) {
    var input = renderer.input();
    if (isPrecise) {
      input.movementSpeed *= 4;
      input.rollSpeed *= 4;
    } else {
      input.movementSpeed /= 4;
      input.rollSpeed /= 4;
    }
  }

  function updateQuery() {
    if (!renderer) return;
    var camera = renderer.camera();

    appConfig.setCameraConfig(camera.position, camera.quaternion);
  }

  function toggleSteering() {
    if (!renderer) return;

    var input = renderer.input();
    var isDragToLookEnabled = input.toggleDragToLook();

    // steering does not require "drag":
    var isSteering = !isDragToLookEnabled;
    appEvents.showSteeringMode.fire(isSteering);
  }

  function clearHover() {
    appEvents.nodeHover.fire({
      nodeIndex: undefined,
      mouseInfo: undefined
    });
  }

  function focusOnNode(nodeId) {
    if (!renderer) return;

    renderer.lookAt(nodeId * 3, highlightFocused);

    function highlightFocused() {
      appEvents.selectNode.fire(nodeId);
    }
  }

  function around(r, x, y, z) {
    renderer.around(r, x, y, z);
  }

  function setPositions(_positions) {
    destroyHitTest();

    positions = _positions;
    focusScene();

    if (!renderer) {
      renderer = unrender(container);
      touchControl = createTouchControl(renderer);
      moveCameraInternal();
      var input = renderer.input();
      input.on('move', clearHover);
    }

    renderer.particles(positions);

    hitTest = renderer.hitTest();
    hitTest.on('over', handleOver);
    hitTest.on('click', handleClick);
    hitTest.on('dblclick', handleDblClick);
    hitTest.on('hitTestReady', adjustMovementSpeed);
  }

  function getColor(c) {
    return colorMap.has(c) ? colorMap.get(c) : defaultNodeColor;
  }
  // 染色
  function setLabels(labels) {
    if (!renderer) return;
    // set color
    var view = renderer.getParticleView();
    var colors = view.colors();
    nodeCommunity = [];  // 存储节点的社区分类
    for (var i = 0; i < labels.length; i++) {
      var country =  labels[i].toString().split('-')[2]
      if (!communityColorMap.has(country)) {
        //构建颜色表
        var c = getColor(8)
        //var c = getColor((i % 7))
        communityColorMap.set(country, c);
      }
      communityColorMap.set("CN", getColor(6));
      communityColorMap.set("US", getColor(7));
      communityColorMap.set("RU", getColor(4));
      communityColorMap.set("UA", getColor(5));
      communityColorMap.set("JP", getColor(1));
      communityColorMap.set("DE", getColor(2));
      colorNode(i * 3, colors, communityColorMap.get(labels[i].toString().split('-')[2]));
      nodeCommunity.push(labels[i].toString().split('-')[2]);
    }
    view.colors(colors);
    // set sizes
  }


  function adjustMovementSpeed(tree) {
    var input = renderer.input();
    if (tree) {
      var root = tree.getRoot();
      input.movementSpeed = root.bounds.half * 0.02;
    } else {
      input.movementSpeed *= 2;
    }
  }

  function focusScene() {
    // need to be within timeout, in case if we are detached (e.g.
    // first load)
    setTimeout(function() {
      container.focus();
    }, 30);
  }

  function setLinks(outLinks, inLinks) {
    links = outLinks;
    lineViewNeedsUpdate = true;
    updateSizes(outLinks, inLinks);
    renderLineViewIfNeeded();
  }

  function updateSizes(outLinks, inLinks) {
    var maxInDegree = getMaxSize(inLinks);
    var view = renderer.getParticleView();
    var sizes = view.sizes();
    for (var i = 0; i < sizes.length; ++i) {
      var degree = inLinks[i];
      if (degree) {
        sizes[i] = ((200 / maxInDegree) * degree.length + 4);
      } else {
        sizes[i] = 4;
      }
    }
    view.sizes(sizes);
  }

  function getMaxSize(sparseArray) {
    var maxSize = 0;
    for (var i = 0; i < sparseArray.length; ++i) {
      var item = sparseArray[i];
      if (item && item.length > maxSize) maxSize = item.length;
    }

    return maxSize;
  }

  function renderLineViewIfNeeded() {
    if (!appConfig.getShowLinks()) return;
    if (!lineView) {
      lineView = createLineView(renderer.scene(), unrender.THREE);
    }
    lineView.render(links, positions);
    lineViewNeedsUpdate = false;
  }

  function toggleLinks() {
    if (lineView) {
      if (lineViewNeedsUpdate) renderLineViewIfNeeded();
      lineView.toggleLinks();
    } else {
      renderLineViewIfNeeded();
    }
  }

  function moveCamera() {
    moveCameraInternal();
  }

  function moveCameraInternal() {
    if (!renderer) return;

    var camera = renderer.camera();
    var pos = appConfig.getCameraPosition();
    if (pos) {
      camera.position.set(pos.x, pos.y, pos.z);
    }
    var lookAt = appConfig.getCameraLookAt();
    if (lookAt) {
      camera.quaternion.set(lookAt.x, lookAt.y, lookAt.z, lookAt.w);
    }
  }

  function destroyHitTest() {
    if (!hitTest) return; // nothing to destroy

    hitTest.off('over', handleOver);
    hitTest.off('click', handleClick);
    hitTest.off('dblclick', handleDblClick);
    hitTest.off('hitTestReady', adjustMovementSpeed);
  }

  function handleClick(e) {
    var nearestIndex = getNearestIndex(positions, e.indexes, e.ray, 30);

    appEvents.selectNode.fire(getModelIndex(nearestIndex));
  }

  function handleDblClick(e) {
    var nearestIndex = getNearestIndex(positions, e.indexes, e.ray, 30);
    if (nearestIndex !== undefined) {
      focusOnNode(nearestIndex/3);
    }
  }

  function handleOver(e) {
    var nearestIndex = getNearestIndex(positions, e.indexes, e.ray, 30);

    highlightNode(nearestIndex);
    appEvents.nodeHover.fire({
      nodeIndex: getModelIndex(nearestIndex),
      mouseInfo: e
    });
  }

  function highlightNode(nodeIndex) {
    var view = renderer.getParticleView();
    var colors = view.colors();
    var sizes = view.sizes();

    if (lastHighlight !== undefined) {
      colorNode(lastHighlight, colors, communityColorMap.get(nodeCommunity[lastHighlight/3]));
      sizes[lastHighlight/3] = lastHighlightSize;
    }

    lastHighlight = nodeIndex;


    if (lastHighlight !== undefined) {
      colorNode(lastHighlight, colors, highlightNodeColor);
      lastHighlightSize = sizes[lastHighlight/3];
      sizes[lastHighlight/3] *= 1.5;
    }

    view.colors(colors);
    view.sizes(sizes);
  }

  function highlightQuery(query, color, scale) {
    if (!renderer) return;

    var nodeIds = query.results.map(toNativeIndex);
    var view = renderer.getParticleView();
    var colors = view.colors();

    for (var i = 0; i < nodeIds.length; ++i) {
      colorNode(nodeIds[i], colors, color)
    }

    view.colors(colors);
    appEvents.queryHighlighted.fire(query, color);
  }

  function colorNode(nodeId, colors, color) {
    var colorOffset = (nodeId/3) * 4;
    colors[colorOffset + 0] = (color >> 24) & 0xff;
    colors[colorOffset + 1] = (color >> 16) & 0xff;
    colors[colorOffset + 2] = (color >> 8) & 0xff;
    colors[colorOffset + 3] = (color & 0xff);
  }

  function highlightLinks(links, color) {
    var lines = new Float32Array(links.length * 3);
    for (var i = 0; i < links.length; ++i) {
      var i3 = links[i] * 3;
      lines[i * 3] = positions[i3];
      lines[i * 3 + 1] = positions[i3 + 1];
      lines[i * 3 + 2] = positions[i3 + 2];
    }
    renderer.lines(lines, color);
  }

  function cls() {
    var view = renderer.getParticleView();
    var colors = view.colors();

    for (var i = 0; i < colors.length/4; i++) {
      colorNode(i * 3, colors, 0xffffffff);
      //colorNode(i*3, colors, defaultNodeColor);
    }

    view.colors(colors);
  }

  function toNativeIndex(i) {
    return i.id * 3;
  }

  function getModelIndex(nearestIndex) {
    if (nearestIndex !== undefined) {
      // since each node represented as triplet we need to divide by 3 to
      // get actual index:
      return nearestIndex/3
    }
  }

  function destroy() {
    var input = renderer.input();
    if (input) input.off('move', clearHover);
    renderer.destroy();
    appEvents.positionsDownloaded.off(setPositions);
    appEvents.linksDownloaded.off(setLinks);

    if (touchControl) touchControl.destroy();
    renderer = null;

    clearInterval(queryUpdateId);
    appConfig.off('camera', moveCamera);
    appConfig.off('showLinks', toggleLinks);

    // todo: app events?
  }
}