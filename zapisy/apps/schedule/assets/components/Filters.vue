<template>
  <div style="margin-bottom: 10px;" id="filter" class="card bg-light">
    <div class="card-body">
      <h5 class="card-title">Filtry wydarzeń</h5>
      <div class="row" v-if="!collapsed">
        <div class="col-md-6">
          <label>Wybierz sale:</label>
          <select class="custom-select" v-model="rooms" title="Wybierz sale" multiple>
            <option value="all">Wszystkie</option>
            <option v-for="room in options.rooms" :value="room.number">
              {{ room.number }} ({{ room.capacity }} miejsc, {{ room.type }})
            </option>
          </select>
        </div>

        <div class="col-md-3">
          <div class="form-group">
            <label>Tytuł lub autor wydarzenia:</label>
            <input class="form-control" placeholder="Seminarium lub Jan Nowak" v-model="title_or_author">
          </div>
          <div class="form-group">
            <label>Miejsce wydarzenia:</label>
            <input class="form-control" placeholder="Sala HS w Instytucie Matematyki" v-model="place">
          </div>
        </div>

        <div class="col-md-3">
          <label>Typ wydarzenia:</label> <br>
          <div class="form-check" v-for="type in options.type">
            <input v-model="types" class="form-check-input" type="checkbox" :value="type.value">
            <label class="form-check-label">{{ type.text }}</label>
          </div>
        </div>
      </div>

      <div class="row" v-if="!collapsed && user_info.is_admin">
        <div class="col-md-12">
          <label>Status wydarzenia:</label><br>
          <div class="form-check form-check-inline" v-for="status in options.status">
            <input v-model="statuses" class="form-check-input" type="checkbox" :value="status.value">
            <label class="form-check-label">{{ status.text }}</label>
          </div>
        </div>
      </div>
    </div>
    <div class="card-footer p-1 text-center">
      <a href="#" @click.prevent="collapsed = !collapsed">Zwiń / Rozwiń</a>
    </div>
  </div>
</template>

<script>
export default {
  name: "Filters",
  data() {
    return {
      collapsed: false,
      url: "",

      rooms: ["all"],
      place: "",
      title_or_author: "",
      types: ["0", "1", "2", "5"],
      statuses: ["0", "1", "2"],

      options: {
        rooms: [],
        type: [
          {value: "0", text: "Egzamin"},
          {value: "1", text: "Kolokwium"},
          {value: "2", text: "Wydarzenie"},
          {value: "3", text: "Zajęcia"},
          // value "4" is no longer supported, as type 'others' is deprecated
          {value: "5", text: "Rezerwacja cykliczna"}
        ],
        status: [
          {value: "0", text: "Oczekujące"},
          {value: "1", text: "Zaakceptowane"},
          {value: "2", text: "Odrzucone"},
        ],
      },

      user_info: {
        full_name: "",
        is_student: false,
        is_employee: false,
        is_admin: false
      },
    }
  },
  created: function () {
    this.fetch_data_from_html();
    this.create_searchparams();
  },
  methods: {
    fetch_data_from_html: function () {
      let rooms_fetched =
          JSON.parse(document.getElementById("classrooms").innerHTML);

      for (let room of rooms_fetched)
        this.options.rooms.push(room);

      this.user_info = JSON.parse(document.getElementById("user_info").innerHTML);
    },

    create_searchparams: function () {
      const search_params = new URLSearchParams('');

      if (this.rooms.length === 1 && this.rooms.includes('all')
          || this.rooms.length === 0)
        search_params.delete('rooms');
      else
        search_params.set("rooms", this.rooms);

      if (this.title_or_author)
        search_params.set("title_author", this.title_or_author);

      if (this.place)
        search_params.set("place", this.place);

      if (this.types.length > 0)
        search_params.set("types", this.types);
      else
        return [];

      if (this.statuses.length > 0)
        search_params.set("statuses", this.statuses);
      else
        return [];

      this.url = search_params.toString();
      return search_params;
    },
    emit_refetch_events: function () {
      this.$emit('refetchEvents');
    }
  },
  watch: {
    // rooms: function () {
    //   this.$emit('refetchEvents');
    // }
    rooms: function () { this.emit_refetch_events(); },
    place: function () { this.emit_refetch_events(); },
    types: function () { this.emit_refetch_events(); },
    statuses: function () { this.emit_refetch_events(); },
    title_or_author: function () { this.emit_refetch_events(); }
  }
}
</script>

<style scoped>

</style>