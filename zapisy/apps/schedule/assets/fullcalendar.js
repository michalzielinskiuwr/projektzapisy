import { Calendar } from "@fullcalendar/core";
import plLocale from "@fullcalendar/core/locales/pl";
import bootstrapPlugin from "@fullcalendar/bootstrap";
import interactionPlugin from "@fullcalendar/interaction";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";

async function fetchEvents(fetchInfo) {
    // let url = new URL("http://127.0.0.1:8000/classrooms/terms/");
    let url = new URL("http://192.168.0.16:8000/classrooms/terms/");
    url.searchParams.set("start", fetchInfo.start.toISOString())
    url.searchParams.set("end", fetchInfo.end.toISOString())

    let room_id = $('#room_selector').val();
    if (room_id === "all")
        url.searchParams.delete('rooms');
    else
        url.searchParams.set("rooms", [room_id]);

    let title_author_input = $('#title_author_input').val();
    if (title_author_input)
        url.searchParams.set("title_author", title_author_input);

    const response = await fetch(url);
    return response.json();
}

// Function handler for creating events
function create_event(timeRange) {
    $('#create_event_modal').modal('show');
    document.getElementById("reservation_date").valueAsDate = new Date();

    // timeRange is specified for events created by selecting hours in calendar
    if (timeRange != null) {
        var start = new Date(timeRange.startStr).toISOString();
        var end   = new Date(timeRange.endStr).toISOString();
        $('#reservation_date').val(start.slice(0, 10));
        $('#reservation_time_start').val(start.slice(11, 16));
        $('#reservation_time_end').val(end.slice(11, 16));
    }

    $('#create_event_button').off('click');
    $('#create_event_button').one('click', function () {
        var name = $('#reservation_name').val().toString();
        var description = $('#reservation_description').val().toString();
        var visibility = ($('#reservation_visibility').val() == 'visible') ? true : false;
        var room = ($('#reservation_room').val() != 'room_none') ? $('#reservation_room').val() : null;
        var place = ($('#reservation_room').val() == 'room_none') ? $('#reservation_place').val() : null;
        var type;
        var startTime = new Date($('#reservation_date').val() + "T" + $('#reservation_time_start').val() + "Z").toISOString();
        var endTime = new Date($('#reservation_date').val() + "T" + $('#reservation_time_end').val() + "Z").toISOString();
        var day = $('#reservation_date').val();
        var start = $('#reservation_time_start').val();
        var end = $('#reservation_time_end').val();
        
        switch ($('#reservation_type').val()) {
            case "type_event":
                type = "2";
                break;
            case "type_exam":
                type = "0";
                break;
            case "type_test":
                type = "1";
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

        // We accept only room or only place, both cannot be specified at the same time
        if (room)
            eventData.terms[0]["room"] = parseInt(room);
        else
            eventData.terms[0]["place"] = place;

        // FullCalendar needs its own object to add the event to calendar, these fields
        // have to be named title, start and end.
        var fullCalendarData = {
            title: name,
            start: startTime,
            end: endTime,
            color: "green"
        }
        calendar.addEvent(fullCalendarData);

        $.post("http://192.168.0.16:8000/classrooms/events/", JSON.stringify(eventData), null, "json");

        $('#create_event_modal').modal('hide');
        calendar.unselect();
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
        select: create_event
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

    // Show input for place only if no room is selected (create event modal)
    $(function () {
        $('#reservation_room').on('change', function () {
            if (this.value == 'room_none')
                $('#reservation_place_div').show();
            else
                $('#reservation_place_div').hide();
        });
    });
});
