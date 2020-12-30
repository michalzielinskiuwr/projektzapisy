import { Calendar } from "@fullcalendar/core";
import plLocale from "@fullcalendar/core/locales/pl";
import bootstrapPlugin from "@fullcalendar/bootstrap";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";

async function fetchEvents(fetchInfo) {
    let url = new URL("http://127.0.0.1:8000/classrooms/terms/");
    //let url = new URL("http://192.168.0.16:8000/classrooms/events/");
    url.searchParams.set("start", fetchInfo.start.toISOString())
    url.searchParams.set("end", fetchInfo.end.toISOString())

    let room_id = $('#room_selector').find("option:selected").attr("value");
    if (room_id === "all")
        url.searchParams.delete('rooms');
    else
        url.searchParams.set("rooms", [room_id]);

    let title_author_input = $('#title_author_input').val()
    if (title_author_input)
        url.searchParams.set("title_author", title_author_input);

    const response = await fetch(url);
    return response.json();
}

let calendarEl, calendar;

document.addEventListener("DOMContentLoaded", function() {
    calendarEl = document.getElementById("calendar");

    calendar = new Calendar(calendarEl, {
        plugins: [dayGridPlugin, timeGridPlugin, bootstrapPlugin],

        themeSystem: "bootstrap",
        initialView: "timeGridWeek",
        locale: plLocale,

        buttonText: {
            prev: "<",
            next: ">",
        },
        height: "auto",

        //allDaySlot: false,
        slotMinTime: "08:00:00",
        slotMaxTime: "22:00:00",

        headerToolbar: {
            start: "prev,next today",
            center: "title",
            end: "timeGridDay,timeGridWeek,dayGridMonth",
        },

        eventDisplay: 'list-item',
        events: fetchEvents,
    });

    calendar.render();

    $('#room_selector').on('change', function() {
        // let filter_id = $(this).find("option:selected").attr("value");
        // console.log("room_selector changed. filter_id = " + filter_id);
        calendar.refetchEvents();
    });
    $('#title_author_input').on('change', function() {
        calendar.refetchEvents();
    });
});
