import { Calendar } from "@fullcalendar/core";
import plLocale from "@fullcalendar/core/locales/pl";
import bootstrapPlugin from "@fullcalendar/bootstrap";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";


async function fetchEvents() {
  let url = new URL("http://127.0.0.1:8000/classrooms/events/");
  const response = await fetch(url);
  return response.json();
}

document.addEventListener("DOMContentLoaded", function () {
  const calendarEl = document.getElementById("calendar");

  const calendar = new Calendar(calendarEl, {
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
});