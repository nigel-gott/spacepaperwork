var regions;
var region_bounds = {};
var stars;
var star_dict = {};
var bases;
var connections;
var route = [];
var svg = document.getElementById('mapSVG');
var svgPanner;
var showLabels = true;
var showBases = true;
var starLabelZoom = 4.5;
var selectedStarId;
var MAPBOT_HOST = MAPBOT_HOST || 'http://127.0.0.1:5000';
var modal = document.querySelector("#modal");
var modalOverlay = document.querySelector("#modal-overlay");

function CloseModal() {
    modal.classList.add("closed");
    modalOverlay.classList.add("closed");
}

function OnStarClick(e)
{
    selectedStarId = this.id;

    title = document.getElementById('modal-title');
    title.innerHTML = star_dict[selectedStarId].name;
    modal.classList.remove("closed");
    modalOverlay.classList.remove("closed");
}

function UpdateBaseClick(baseLevel) {
    CloseModal();
    base_json = {
        'star_index': selectedStarId,
        'current_base_level': baseLevel,
        'reported_by': 'unknown'
    };
    $.ajax({
        url: MAPBOT_HOST + "/api/v1/resources/bases",
        type: "PUT",
        contentType: "application/json",
        dataType: 'json',
        data: JSON.stringify(base_json),
        crossDomain: true
    }).then(function(data) {
        console.log("Bases data for " + selectedStarId + " updated");
        bases.push({ 'star_index': selectedStarId, 'current_base_level': baseLevel});
        UpdateMap();
    });

}

function OnStarEnter(e)
{
    // get all the connections that start or end with this star id
    connections.forEach(c => {
        if(c.star_index1 == this.id || c.star_index2 == this.id) {
            let id = c.star_index1 + '_' + c.star_index2;
            elem = document.getElementById(id);
            if(elem !== null)
                elem.classList.add('connection_select');
        }
    });
    // update the label
    // elem = document.getElementById(this.id + "_label");
    // elem.classList = ['star_label_select'];
}

function OnStarLeave(e)
{
    // get all the connections that start or end with this star id
    connections.forEach(c => {
        if(c.star_index1 == this.id || c.star_index2 == this.id) {
            let id = c.star_index1 + '_' + c.star_index2;
            elem = document.getElementById(id);
            if(elem !== null)
                elem.classList.remove('connection_select');
        }
    });
    // update the label
    // elem = document.getElementById(this.id + "_label");
    // elem.classList = ['star_label'];
}

function OnRegionSelect(e)
{
    region = document.getElementById('map_region_select').value;
    // zoom and pan to the selected region
    //svgPanner
    //region_bounds
    svgPanner.resetZoom();
    svgPanner.resetPan();

    var svg_bbox = svg.getBoundingClientRect(); // get the bounding rectangle
    cx = svg_bbox.width / 2.0;
    cy = svg_bbox.height / 2.0;
    console.log(cx);
    console.log(cy);
    p = {x: cx - region_bounds[region]['center-x'], y: cy - region_bounds[region]['center-z']};
    svgPanner.pan(p);
    svgPanner.zoom(5.0);
    ShowStarLabels();

}

function ShowRoute(newRoute)
{
    // clear old route
    if(route != null)
    {
        route_uc = [];
        route.forEach(r => {
            r_uc = r.toUpperCase();
            e = document.getElementById(r_uc);
            e.classList.remove('route');
            route_uc.push(r_uc);
        });
        connections.forEach(c => {
            if(route_uc.includes(c.star_index1) || route_uc.includes(c.star_index2)) {
                let key1 = c.star_index1 + '_' + c.star_index2;
                elem = document.getElementById(key1);
                if(elem !== null)
                    elem.classList.remove('route');
            }
        });
    }
    route = newRoute;
    routeWindow = document.getElementById('route_window');

    if(newRoute.length > 0)
    {
        routeText = '<b>Route (' + route.length + ')</b><br/>\n';
        // hilight new route
        route.forEach(r => {
            e = document.getElementById(r.toUpperCase());
            e.classList.toggle('route');
            routeText += r + "<br />\n";
        });
        routeWindow.innerHTML = routeText;
        routeWindow.classList.remove('closed');

        for(i = 0; i < route.length - 1; i++)
        {
            let key1 = route[i] + '_' + route[i+1];
            let key2 = route[i+1] + '_' + route[i];
            elem = document.getElementById(key1.toUpperCase());
            if(elem !== null)
                elem.classList.add('route');
            elem = document.getElementById(key2.toUpperCase());
            if(elem !== null)
                elem.classList.add('route');
        }
    } else {
        routeWindow.classList.add('closed');
    }
}

function OnClickRoute()
{
    let start = document.getElementById('map_system_1').value.toUpperCase();
    let end = document.getElementById('map_system_2').value.toUpperCase();
    $.ajax({
        url: MAPBOT_HOST + "/api/v1/resources/route/" + start + "/" + end,
        type: "GET",
        contentType: "application/json",
        crossDomain: true
    }).then(function(data) {
        ShowRoute(data);
    });
}

function CreateStarDict()
{
    stars.forEach(s => {
        star_dict[s.star_index] = s;
    });
}

function CalculateRegionBounds()
{
    regions.forEach(r => {
        region_bounds[r] = {
            'name': r,
            'min-x': 1000.0,
            'min-y': 1000.0,
            'min-z': 1000.0,
            'max-x': -1000.0,
            'max-y': -1000.0,
            'max-z': -1000.0,
            'center-x': 0.0,
            'center-y': 0.0,
            'center-z': 0.0
        }
    });

    stars.forEach(s => {
        r = region_bounds[s.region];
        if(s.x < r['min-x'])
            r['min-x'] = s.x;
        if(s.y < r['min-y'])
            r['min-y'] = s.y;
        if(s.z < r['min-z'])
            r['min-z'] = s.z;

        if(s.x > r['max-x'])
            r['max-x'] = s.x;
        if(s.y > r['max-y'])
            r['max-y'] = s.y;
        if(s.z > r['max-z'])
            r['max-z'] = s.z;

    });

    regions.forEach(r => {
        rb = region_bounds[r];
        rb['center-x'] = (rb['min-x'] + rb['max-x']) / 2.0;
        rb['center-y'] = (rb['min-y'] + rb['max-y']) / 2.0;
        rb['center-z'] = (rb['min-z'] + rb['max-z']) / 2.0;
    });
}

function CreateStarLabel(starId, current_base_level=null)
{
    s = star_dict[starId];

    label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.id = s.star_index + '_label';
    label.setAttributeNS(null, 'visibility', 'hidden');
    label.setAttributeNS(null, 'x', s.x + 0.6);
    label.setAttributeNS(null, 'y', s.z);

    label.classList.add('star_label');
    label.textContent = s.name;
    svg.appendChild(label);

    base = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    base.id = s.star_index + '_base';
    base.setAttributeNS(null, 'visibility', 'hidden');
    base.setAttributeNS(null, 'x', s.x + 0.6);
    base.setAttributeNS(null, 'y', s.z + 1.2);
    base.classList.add('star_label');
    if(current_base_level == null)
        current_base_level = '?'
    base.textContent = current_base_level + '/' + s.max_base_level;
    svg.appendChild(base);
}

function UpdateStarLabel(starId, current_base_level=null)
{
    s = star_dict[starId];

    base = document.getElementById(starId + "_base");
    base.textContent = current_base_level + '/' + s.max_base_level;
}

function ShowStarLabels()
{
    stars.forEach(s => {
        label = document.getElementById(s.star_index + "_label");

        if(showLabels)
            label.setAttributeNS(null, 'visibility', 'visible');

        if(showBases)
        {
            base = document.getElementById(s.star_index + "_base");
            base.setAttributeNS(null, 'visibility', 'visible');
        }
    });
}

function HideStarLabels()
{
    stars.forEach(s => {
        label = document.getElementById(s.star_index + "_label");
        base = document.getElementById(s.star_index + "_base");

        label.setAttributeNS(null, 'visibility', 'hidden');
        base.setAttributeNS(null, 'visibility', 'hidden');
    });
}

function UpdateMap()
{
    bases.forEach(b => {
        star = star_dict[b.star_index];
        star_element = document.getElementById(b.star_index);
        base_label = document.getElementById(b.star_index + "_base");
        star_class = 'base-' + b.current_base_level;
        // remove any existing base-# classes
        for(var i = star_element.classList.length - 1; i > -1; i--) {
            if(star_element.classList[i].includes('base-')) {
                star_element.classList.remove(star_element.classList[i]);
            }
        }
        star_element.classList.add(star_class);
        UpdateStarLabel(b.star_index, b.current_base_level);

    });
}

function UpdateBases()
{
    console.log("Downloading bases data");
    $.ajax({
        url: MAPBOT_HOST + "/api/v1/resources/bases/all",
        type: "GET",
        crossDomain: true
    }).then(function(data) {
        console.log("Bases data loaded");
        // todo - compare new bases to old bases & remove stale entries
        bases = data;
        UpdateMap();
    });
}

var oldMapScale;
function OnMapZoom(newMapScale) {
    if(newMapScale > oldMapScale)
    {
        // zooming in
        if(newMapScale > starLabelZoom && oldMapScale <= starLabelZoom)
        {
            ShowStarLabels();
        }
    }
    else
    {
        // zooming out
        if(newMapScale < starLabelZoom && oldMapScale >= starLabelZoom)
        {
            HideStarLabels();
        }
    }

    oldMapScale = newMapScale;
}

function CreateIconITC(x, y)
{
    // 12 points
    points = [];

    points[0] = [x + 0.75, y + -0.75];
    points[1] = [x + 0.75, y + -0.5];
    points[2] = [x + 1.5, y + -0.5];
    points[3] = [x + 1.5, y + 0.5];
    points[4] = [x + 0.75, y + 0.5];
    points[5] = [x + 0.75, y + 0.75];
    points[6] = [x + -0.75, y + 0.75];
    points[7] = [x + -0.75, y + 0.5];
    points[8] = [x + -1.5, y + 0.5];
    points[9] = [x + -1.5, y + -0.5];
    points[10] = [x + -0.75, y + -0.5];
    points[11] = [x + -0.75, y + -0.75];

    return points;
}

function CreateMap()
{
    CreateStarDict();
    CalculateRegionBounds();

    // clear the map
    $("#mapSVG").empty();

    // SVG Rendering
    svg.setAttributeNS(null, 'viewBox', '0 0 1000 1000');

    console.log('Rendering region names')
    regions.forEach(r => {
        rb = region_bounds[r];
        label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.id = r + '_label';
        label.setAttributeNS(null, 'x', rb['center-x']);
        label.setAttributeNS(null, 'y', rb['center-z']);
        label.classList.add('region_label');
        label.textContent = r;
        svg.appendChild(label);
    });

    console.log('Rendering connections')
    // The connections DB has A->B as well as B->A
    // we only want to render that once
    conn_dict = {};
    connections.forEach(c => {
        key1 = c.star_index1 + '_' + c.star_index2;
        key2 = c.star_index2 + '_' + c.star_index1;

        if(!(key1 in conn_dict))
        {
            star1 = star_dict[c.star_index1];
            star2 = star_dict[c.star_index2];

            var element = document.createElementNS('http://www.w3.org/2000/svg','line');
            element.id = c.star_index1 + '_' + c.star_index2
            element.setAttribute('x1',star1.x);
            element.setAttribute('y1',star1.z);
            element.setAttribute('x2',star2.x);
            element.setAttribute('y2',star2.z);
            element.classList.add('connection');
            if(c.regional_gate)
                element.classList.add('connection_region');

            svg.appendChild(element);

            //conn_dict[key1] = true;
            conn_dict[key2] = true;
            conn_dict[key1] = true;
        }
    });

    console.log('Rendering stars')
    stars.forEach(s => {
        if(s.has_itc) {
            // render ITCS as a hash shape
            var element = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
            element.id = s.star_index;
            element.classList.add('star');
            points = CreateIconITC(s.x, s.z);
            for(point of points) {
                p = svg.createSVGPoint();
                p.x = point[0];
                p.y = point[1];
                element.points.appendItem(p);
            }

            element.onclick = OnStarClick;
            element.onmouseenter = OnStarEnter;
            element.onmouseleave = OnStarLeave;

            tooltip = document.createElementNS('http://www.w3.org/2000/svg', 'title');
            tooltip.innerHTML =
                s.name +
                "\nSec Status: " + s.security_level +
                "\nConstellation: " + s.constellation +
                "\nRegion: " + s.region;

            element.appendChild(tooltip);

            svg.appendChild(element);
        } else if(s.has_station) {
            var element = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            element.id = s.star_index;
            element.setAttributeNS(null, 'x', s.x - 0.5);
            element.setAttributeNS(null, 'y', s.z - 0.5);
            element.setAttributeNS(null, 'width', 1.0);
            element.setAttributeNS(null, 'height', 1.0);
            element.classList.add('star');
            element.onclick = OnStarClick;
            element.onmouseenter = OnStarEnter;
            element.onmouseleave = OnStarLeave;

            tooltip = document.createElementNS('http://www.w3.org/2000/svg', 'title');
            tooltip.innerHTML =
                s.name +
                "\nSec Status: " + s.security_level +
                "\nConstellation: " + s.constellation +
                "\nRegion: " + s.region;
            element.appendChild(tooltip);

            svg.appendChild(element);

        } else {
            var element = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            element.id = s.star_index;
            element.setAttributeNS(null, 'cx', s.x);
            element.setAttributeNS(null, 'cy', s.z);
            element.setAttributeNS(null, 'r', 0.5);
            element.classList.add('star');
            element.onclick = OnStarClick;
            element.onmouseenter = OnStarEnter;
            element.onmouseleave = OnStarLeave;

            tooltip = document.createElementNS('http://www.w3.org/2000/svg', 'title');
            tooltip.innerHTML =
                s.name +
                "\nSec Status: " + s.security_level +
                "\nConstellation: " + s.constellation +
                "\nRegion: " + s.region;
            element.appendChild(tooltip);

            svg.appendChild(element);
        }
        CreateStarLabel(s.star_index);
    });

    console.log('done');

    svgPanner = svgPanZoom(svg, {
        panEnabled: true,
        zoomEnabled: true,
        contain: false,
        fit: false,
        onZoom: OnMapZoom,
        maxZoom: 30.0
    });

    UpdateBases();
    ShowRoute(route);
    setInterval(UpdateBases, 30000);

    /*
    // Canvas Rendering
    console.log('Rendering stars')
    var canvas = document.getElementById("mapCanvas");
    var ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#000000";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#FFFFFF";
    ctx.strokeStyle = "#FFFFFF";
    stars.forEach(s => {
        ctx.beginPath();
        ctx.arc(s.x, s.z, 1.0, 0, 2 * Math.PI);
        ctx.stroke();
    });

    console.log('Rendering connections')
    ctx.lineWidth = 1.0;

    connections.forEach(c => {
        star1 = star_dict[c.star_index1];
        star2 = star_dict[c.star_index2];
        ctx.strokeStyle = "#FFFFFF";
        ctx.moveTo(star1.x, star1.z);
        ctx.lineTo(star2.x, star2.z);
        ctx.stroke();
    });
    console.log('done');
    */
}

function LoadRegionData(){
    console.log("Downloading region data");
    return $.ajax({
        url: MAPBOT_HOST + "/api/v1/resources/regions/all",
        type: "GET",
        crossDomain: true
    }).then(function(data) {
        console.log("Region data loaded");
        regions = data;
        region_select = document.getElementById('map_region_select');
        for(var i = region_select.length - 1; i > -1; i--)
        {
            region_select.remove(i);
        }
        o = document.createElement('option');
        o.text = 'None';
        region_select.add(o);
        regions.forEach(r => {
            o = document.createElement('option');
            o.text = r;
            o.value = r;
            region_select.add(o);
        });
    });
}

function LoadStarData(){
    console.log("Downloading star data");
    return $.ajax({
        url: MAPBOT_HOST + "/api/v1/resources/stars/all",
        type: "GET",
        crossDomain: true
    }).then(function(data) {
        console.log("Star data loaded");
        stars = data;
    });
}

function LoadConnectionData(){
    console.log("Downloading connection data");
    return $.ajax({
        url: MAPBOT_HOST + "/api/v1/resources/connections/all",
        type: "GET",
        crossDomain: true
    }).then(function(data) {
        console.log("Connection loaded");
        connections = data;
    });
}

function OnLoad()
{
    LoadRegionData()
        .then(LoadStarData())
        .then(LoadConnectionData)
        .then(CreateMap);
}

$(document).ready(OnLoad);
