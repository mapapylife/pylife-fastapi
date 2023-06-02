'use strict';

var map = null;
var rc = null;

var layers = {};
var markers = {};
var last_update = null;


function setupLeaflet() {
    // create the map
    map = L.map('map');

    // assign map and image dimensions
    rc = new L.RasterCoords(map, [6000, 6000], 5.415);

    // set max zoom Level (might be `x` if gdal2tiles was called with `-z 0-x` option)
    map.setMaxZoom(7);

    // set the view in the center of the image
    map.setView(rc.unproject([3000, 3000]), 4);

    // the tile layer containing the image generated with gdal2tiles.py
    L.tileLayer('https://mapapylife.github.io/tilemap/{z}/{x}/{y}.png', {
        attribution: 'Map data &copy; <a href="https://panel.pylife-rpg.pl/">Play Your Life</a>, Imagery &copy; <a href="https://github.com/Patrick2562/mtasa-map-images/">Patrick2562</a>',
        noWrap: true
    }).addTo(map);

    // layer groups
    layers = {
        zones: L.featureGroup(),
        houses: L.featureGroup(),
        blips: L.featureGroup(),
        events: L.featureGroup(),
        other: L.featureGroup()
    };

    // map containing zones and houses by id
    markers = {
        zones: {},
        houses: {}
    };

    // set last update timestamp to 0
    last_update = 0;

    // remove markers that are outside view bounds to improve performance
    map.on('zoomend moveend resize zoom move', function() {
        for (var layer in layers) {
            if (layer === 'zones') {
                continue;
            }

            checkVisibility(layer);
        }
    });

    // disable maxBounds as it causes headache
    map.setMaxBounds();
}


function setupTypeahead() {
    var inputSearch = document.getElementById('search');
    $(inputSearch).typeahead({
        items: 10,
        minLength: 2,
        delay: 200,
        theme: 'bootstrap4',
        fitToElement: true,
        selectOnBlur: false,
        changeInputOnSelect: false,
        changeInputOnMove: false,
        source: function(query, process) {
            $.get('/api/v1/search/?query=' + encodeURI(query.trim().toLowerCase()), function(data) {
                process(data);
            });
        },
        matcher: function(item) {
            // check if query keywords are contained in item
            var keywords = this.query.split(' ');
            var match = true;

            keywords.forEach(function(keyword) {
                if (item.name.toLowerCase().indexOf(keyword.toLowerCase()) === -1) {
                    match = false;
                }
            });

            return match;
        },
        highlighter: function(text, item) {
            return typeof item !== 'undefined' && typeof item.highlighted != 'undefined' ? item.highlighted : text;
        },
        icon: function(item) {
            switch (item.group) {
                case 'zones':
                    return '<i class="fa fa-map-marker fa-fw"></i> ';
                case 'houses':
                    return '<i class="fa fa-home fa-fw"></i> ';
                case 'jobs':
                    return '<i class="fa fa-briefcase fa-fw"></i> ';
                default:
                    return '<i class="fa fa-question-circle fa-fw"></i> ';
            }
        },
        afterSelect: function(item) {
            // if item was selected on dropdown
            if ($('.typeahead').is(':visible')) {
                if (item.group === 'zones') {
                    var zone = markers.zones[item.id];
                    showZoneOnMap(zone);
                } else if (item.group === 'houses') {
                    var house = markers.houses[item.id];
                    showHouseOnMap(house);
                }
            }

            // close navbar on mobile devices
            if ($('.navbar-collapse').hasClass('collapse show')) {
                $('.navbar-collapse').collapse('hide');
            }

            inputSearch.value = '';
            inputSearch.blur();
        }
    });
}


function getHouseIcon(house) {
    if (house.owner) {
        return L.icon({iconUrl: '/static/icons/Icon_32.png', iconSize: [16, 16]});
    } else {
        return L.icon({iconUrl: '/static/icons/Icon_31.png', iconSize: [16, 16]});
    }
}


function getIcon(iconName) {
    return L.icon({iconUrl: '/static/' + iconName, iconSize: [16, 16]});
}


function getZonePopupText(zone) {
    var popupText = '<dl><dt>' + zone.name + '</dt><dd>' + zone.description + '</dd>';
    var houses = getHousesInZone(zone);

    if (houses.length > 0) {
        var available = 0, total = 0;

        houses.forEach(function(house) {
            if (house.owner === null) {
                available++;
            }

            total += house.price;
        });

        var averagePrice = parseFloat(total / houses.length).toFixed(2);
        popupText += '<dt><i class="fa fa-home fa-fw"></i> Ilość domów:</dt><dd>' + available + '/' + houses.length + ' dostępne</dd>';
        popupText += '<dt><i class="fa fa-money fa-fw"></i> Średnia cena:</dt><dd>' + formatPrice(averagePrice) + '€ za dobę</dd></dl>';
    } else {
        popupText += '<dd>Brak domów na wynajem!</dd></dl>';
    }

    return popupText;
}


function getHousePopupText(house) {
    var popupText = '<dl><dt>' + house.id  + '. ' + house.title + '</dt><dd>' + house.location + '</dd>';

    if (house.owner) {
        popupText += '<dt><i class="fa fa-user fa-fw"></i> Właściciel:</dt><dd>' + house.owner + '</dd>';
        popupText += '<dt><i class="fa fa-money fa-fw"></i> Cena:</dt><dd>' + formatPrice(house.price) + '€ za dobę</dd>';
        popupText += '<dt><i class="fa fa-calendar fa-fw"></i> Wynajęty do:</dt><dd>' + formatDate(house.expires) + '</dd>';
    } else {
        popupText += '<dd>Do wynajęcia!<dd>';
        popupText += '<dt><i class="fa fa-money fa-fw"></i> Cena:</dt><dd>' + house.price + '€ za dobę</dd>';
    }

    popupText += '</dl>';
    return popupText;
}


function getEventPopupText(event) {
    var popupText = '<dl><dt>' + event.name + '</dt><dd>' + event.location + '</dd>' +
        '<dt><i class="fa fa-info fa-fw"></i> Opis wydarzenia:</dt><dd>' + event.description + '</dd>';

    if (event.start_date) {
        popupText += '<dt><i class="fa fa-calendar-check-o fa-fw"></i> Czas trwania:</dt><dd>Od ' + formatDate(event.start_date) + ' do ';

        if (event.end_date) {
            popupText +=  formatDate(event.end_date);
        } else {
            popupText += 'odwołania';
        }

        popupText += '</dd>';
    }

    popupText += '<dd><a href="' + event.post_url + '" target="_blank">Sprawdź wydarzenie na forum</a></dl>';
    return popupText;
}


function createZonePolygon(zone) {
    var points = zone.points.map(function(point) {
        if (point.length === 2) {
            return rc.unproject(point);
        } else {
            return point.map(function(point) {
                return rc.unproject(point);
            });
        }
    });

    return L.polygon(points, {id: zone.id, name: zone.name, description: zone.description});
}


function createHouseMarker(house) {
    var marker = L.marker(rc.unproject([house.x, house.y]), {id: house.id, icon: getHouseIcon(house)});
    marker.bindPopup(L.responsivePopup().setContent(getHousePopupText(house)));

    return marker;
}


function createBlipMarker(blip) {
    var marker = L.marker(rc.unproject([blip.x, blip.y]), {id: blip.id, icon: getIcon(blip.icon)});
    marker.bindPopup(L.responsivePopup().setContent('<dd>' + blip.name + '</dd>'));

    return marker;
}


function createEventMarker(event) {
    var marker = L.marker(rc.unproject([event.x, event.y]), {id: event.id, icon: getIcon('icons/Icon_53.png')});
    marker.bindPopup(L.responsivePopup().setContent(getEventPopupText(event)));

    return marker;
}


function getHousesInZone(zone) {
    return Object.values(markers.houses).filter(function(house) {
        return house.location === zone.name;
    });
}


function showZoneOnMap(zone) {
    var polygon = layers.zones.getLayer(zone.layer);
    polygon.bindPopup(L.responsivePopup().setContent(getZonePopupText(zone)));

    // close existing popups
    map.closePopup();

    map.flyToBounds(polygon.getBounds());
    map.once('moveend', function() {
        polygon.addTo(map).openPopup();
        polygon.on('popupclose', function() {
            map.removeLayer(polygon);
        });
    });
}

function showHouseOnMap(house) {
    var marker = layers.houses.getLayer(house.layer);
    map.closePopup();

    map.flyTo(marker.getLatLng());
    map.once('moveend', function() {
        marker.openPopup();
    });
}


function loadData() {
    // load zone polygons
    $.getJSON('/api/v1/points/zones', function(json) {
        json.data.forEach(function(zone) {
            var layer = createZonePolygon(zone).addTo(layers.zones);
            markers.zones[zone.id] = {
                name: zone.name,
                description: zone.description,
                layer: layers.zones.getLayerId(layer)
            };
        });
    });

    // load house markers
    $.getJSON('/api/v1/points/houses', function(json) {
        last_update = parseTimestamp(json.last_update);

        json.data.forEach(function(house) {
            var layer = createHouseMarker(house).addTo(layers.houses);
            markers.houses[house.id] = {
                name: house.name,
                location: house.location,
                owner: house.owner,
                price: house.price,
                layer: layers.houses.getLayerId(layer)
            };
        });

        checkVisibility('houses');
    });

    // load blip markers
    $.getJSON('/api/v1/points/blips', function(json) {
        json.data.forEach(function(blip) {
            createBlipMarker(blip).addTo(layers.blips);
        });

        checkVisibility('blips');
    });

    // load event markers
    $.getJSON('/api/v1/points/events', function(json) {
        json.data.forEach(function(event) {
            createEventMarker(event).addTo(layers.events);
        });

        checkVisibility('events');
    });
}


function checkVisibility(layer) {
    layers[layer].eachLayer(function(layer) {
        if (map.getBounds().contains(layer.getLatLng())) {
            map.addLayer(layer);
        } else {
            map.removeLayer(layer);
        }
    });
}


function formatPrice(price) {
    return price.toString().replace('.', ',');
}


function formatDate(timestamp) {
    return dayjs(timestamp).format('YYYY-MM-DD HH:mm');
}


function parseTimestamp(timestamp) {
    return parseInt(new Date(timestamp).getTime() / 1000, 10);
}


function setCookie(name, value, expiry) {
    var date = new Date();
    date.setTime(date.getTime() + (expiry * 24 * 60 * 60 * 1000));
    document.cookie = name + '=' + value + ';expires=' + date.toUTCString() + ';path=/';
}


function getCookie(name) {
    var prefix = name + '=';
    var decodedCookie = decodeURIComponent(document.cookie);

    var ca = decodedCookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }

        if (c.indexOf(prefix) == 0) {
            return c.substring(prefix.length, c.length);
        }
    }

    return null;
}


function init() {
    setupLeaflet();
    setupTypeahead();

    // load all map data
    loadData();

    // check every minute for updates
    setInterval(function() {
        $.getJSON('/api/v1/points/houses?last_update=' + last_update, function(json) {
            var refresh = false;

            // update last update timestamp if last_update is not null
            last_update = json.last_update ? parseTimestamp(json.last_update) : last_update;

            // update house markers
            json.data.forEach(function(house) {
                var marker = null;

                if (markers.houses[house.id]) {
                    marker = layers.houses.getLayer(markers.houses[house.id].layer);
                    marker.setIcon(getHouseIcon(house));
                    marker.setPopupContent(getHousePopupText(house));
                } else {
                    marker = createHouseMarker(house).addTo(layers.houses);
                    refresh = true;
                }

                markers.houses[house.id] = {
                    name: house.name,
                    location: house.location,
                    owner: house.owner,
                    price: house.price,
                    layer: layers.houses.getLayerId(marker)
                };
            });

            // refresh if houses were updated
            if (refresh) {
                checkVisibility('houses');
            }
        });
    }, 60000);
}


$(document).ready(function() {
    init();

    // show welcome modal
    if (!getCookie('cookieconsent_status')) {
        $('#welcome').modal('show');
    }

    $('#accept').click(function() {
        $('#welcome').modal('hide');
        setCookie('cookieconsent_status', 'dismiss', 365);
    });
});
