import { Calendar } from "@fullcalendar/core";
import plLocale from "@fullcalendar/core/locales/pl";
import bootstrapPlugin from "@fullcalendar/bootstrap";
import interactionPlugin from "@fullcalendar/interaction";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";

const event_status = {
    "pending":  "0",
    "accepted": "1",
    "rejected": "2"
};

const event_type = {
    "exam":  "0",
    "test":  "1",
    "event": "2",
    "class": "3",
    "other": "4",
    "special_reservation": "5"
};

const event_color = {
    "invisible": "#d3bb5a",
    "user_is_author": "#8ed35a",
    "pending": "#f00", // "#c371ef",
    "accepted": "#0f0",
    "rejected": "#c13333",
    // Type colors are used to mark events
    "type_exam":  "#ff0",
    "type_test":  "#ff3399",
    "type_event": "#0066ff",
    "type_class": "#003300",
    "type_other": "#ffcc00",
    "type_special_reservation": "#009900"
};

async function fetchEvents(fetchInfo) {
    let url = new URL("classrooms/terms/", window.location.origin);
    url.searchParams.set("start", fetchInfo.start.toISOString());
    url.searchParams.set("end", fetchInfo.end.toISOString());

    let room_id = $('#room_selector').val();
    if (room_id === "all")
        url.searchParams.delete('rooms');
    else
        url.searchParams.set("rooms", [room_id]);

    let title_author_input = $('#title_author_input').val();
    if (title_author_input)
        url.searchParams.set("title_author", title_author_input);

    var types = [];
    if ($('#exam_checkbox').is(':checked'))                 types.push(event_type.exam);
    if ($('#test_checkbox').is(':checked'))                 types.push(event_type.test);
    if ($('#event_checkbox').is(':checked'))                types.push(event_type.event);
    if ($('#classes_checkbox').is(':checked'))              types.push(event_type.class);
    if ($('#other_checkbox').is(':checked'))                types.push(event_type.other);
    if ($('#special_reservation_checkbox').is(':checked'))  types.push(event_type.special_reservation);

    if (types.length > 0)
        url.searchParams.set("types", types);
    else
        return [];

    var fetchedEvents = $.getJSON(url, function (data) {
        for (var i = 0; i < data.length; i++) {
            // Set colors for fetched events
            switch (data[i]['type']) {
                case event_type.exam:  data[i]['color'] = event_color.type_exam;
                                       data[i]['textColor'] = "black"; break;
                case event_type.test:  data[i]['color'] = event_color.type_test; break;
                case event_type.event: data[i]['color'] = event_color.type_event; break;
                case event_type.class: data[i]['color'] = event_color.type_class; break;
                case event_type.other: data[i]['color'] = event_color.type_other; break;
                case event_type.special_reservation: data[i]['color'] = event_color.type_special_reservation; break;
            }

            if(data[i]['visible'] == false)
                data[i]['color'] = event_color.invisible;

            switch (data[i]['status']) {
                case event_status.pending: data[i]['borderColor'] = event_color.pending; break;
                case event_status.accepted: data[i]['borderColor'] = event_color.accepted; break;
                case event_status.rejected: data[i]['borderColor'] = event_color.rejected; break;
            }
        }
    });
    return fetchedEvents;
}

// Function handler for creating events
function create_event(timeRange) {
    $('#create_event_modal').modal('show');
    calendar.unselect();
    document.getElementById("reservation_date").valueAsDate = new Date();

    // timeRange is specified for events created by selecting hours in calendar
    if (timeRange != null) {
        var start = new Date(timeRange.startStr).toISOString();
        var end   = new Date(timeRange.endStr).toISOString();
        $('#reservation_date').val(start.slice(0, 10));
        $('#reservation_time_start').val(start.slice(11, 16));
        $('#reservation_time_end').val(end.slice(11, 16));

        calendar.addEvent({
            id: "temp",
            title: "Nowe wydarzenie (wstępny termin)",
            start: start,
            end: end,
            color: "pink"
        })
    }

    $('#create_event_button').off('click');
    $('#create_event_button').one('click', function () {
        var name = $('#reservation_name').val().toString();
        var description = $('#reservation_description').val().toString();
        var visibility = ($('#reservation_visibility').val() == 'visible') ? true : false;
        var rooms = ($('#reservation_room').val() != 'room_none') ? $('#reservation_room').val() : null;
        var place = ($('#reservation_room').val() == 'room_none') ? $('#reservation_place').val() : null;
        var type;
        var day = $('#reservation_date').val();
        var start = $('#reservation_time_start').val();
        var end = $('#reservation_time_end').val();

        switch ($('#reservation_type').val()) {
            case "type_event":
                type = event_type.event;
                break;
            case "type_exam":
                type = event_type.exam;
                break;
            case "type_test":
                type = event_type.test;
                break;
        }

        var eventData = {
            "title": name,
            "description": description,
            "visible": visibility,
            "type": type,
            "terms": [
                {
                    "day": day,
                    "start": start,
                    "end": end,
                },
            ]
        };

        eventData.terms[0]["room"] = rooms;
        eventData.terms[0]["place"] = place ? place : "";

        console.log("???", JSON.stringify(eventData));
        $.post("events/", JSON.stringify(eventData), calendar.refetchEvents(), "json");

        $('#create_event_modal').modal('hide');
        calendar.unselect();
        calendar.refetchEvents();
    });
}

let calendarEl, calendar;

document.addEventListener("DOMContentLoaded", function() {
    calendarEl = document.getElementById("calendar");

    calendar = new Calendar(calendarEl, {
        plugins: [ interactionPlugin, timeGridPlugin, dayGridPlugin, bootstrapPlugin ],

        themeSystem: "bootstrap",
        initialView: "timeGridWeek",
        locale: plLocale,
        timeZone: "UTC",

        buttonText: {
            prev: "<",
            next: ">",
        },
        height: "auto",
        navLinks: true,

        allDaySlot: false,
        slotMinTime: "08:00:00",
        slotMaxTime: "22:00:00",

        headerToolbar: {
            start: "prev,next today",
            center: "title",
            end: "timeGridDay,timeGridWeek,dayGridMonth",
        },

        eventDisplay: 'list-item',
        events: fetchEvents,

        selectable: true,
        selectMirror: true,
        select: create_event,

        eventClick: function (info) {
            // info.jsEvent.preventDefault(); // do not redirect to given url, display info in modal
            console.log(info.event.title);
        }
    });

    calendar.render();

    $('#room_selector').on('change', function() {
        calendar.refetchEvents();
    });

    $('#title_author_input').on('input', function() {
        calendar.refetchEvents();
    });

    $('#create_event_noselect').one('click', function () {
        create_event(null);
    });

    $('#event_type').contents().find(':checkbox').bind('change', function () {
        calendar.refetchEvents();
    })

    // Show input for place only if no room is selected (create event modal)
    $(function () {
        $('#reservation_room').on('change', function () {
            if (this.value == 'room_none')
                $('#reservation_place_div').show();
            else
                $('#reservation_place_div').hide();
        });
    });

    $('#create_event_modal').on('hidden.bs.modal', function () {
        if (calendar.getEventById("temp"))
            calendar.getEventById("temp").remove();
    });
});
