<script lang="ts">
import Vue from "vue";
import { mapGetters } from "vuex";
import { DefectInfo } from "./store/defects";
import SorterField from "@/theses/assets/components/sorters/SorterField.vue";
import Component from "vue-class-component";

@Component({
  components: {
    SorterField,
  },
  computed: {
    ...mapGetters("defects", {
      defects: "defects",
    }),
    ...mapGetters("filters", {
      tester: "visible",
    }),
    ...mapGetters("sorting", {
      compare: "compare",
      isEmpty: "isEmpty",
    }),
  },
})
export default class DefectList extends Vue {
  // The list should be initialised to contain all the defects and then apply
  // filters and sorting whenever they update.
  visibleDefects: DefectInfo[] = [];

  defects!: DefectInfo[];
  tester!: (_: DefectInfo) => boolean;
  compare!: (a: DefectInfo, b: DefectInfo) => number;

  created() {
    this.$store.dispatch("defects/initFromJSONTag");
  }

  mounted() {
    this.visibleDefects = this.defects;
    this.visibleDefects = this.defects.sort(this.compare);

    this.$store.subscribe((mutation, state) => {
      switch (mutation.type) {
        case "filters/registerFilter":
          this.visibleDefects = this.defects // .filter(this.tester);
          this.visibleDefects.sort(this.compare);
          break;
        case "sorting/changeSorting":
          this.visibleDefects = this.defects // .filter(this.tester);
          this.visibleDefects.sort(this.compare);
          break;
      }
    });
  }
}
</script>

<style scoped>
.selection-none {
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
}
</style>

<template>
  <table class="table table-hover selection-none table-responsive-md">
    <thead id="table-header">
      <tr class="text-center">
        <th>
          <SorterField property="name" label="Nazwa Usterki" />
        </th>
        <th>
          <SorterField property="place" label="Miejsce usterki" />
        </th>
        <th>
          <SorterField property="state" label="Stan Usterki" />
        </th>
        <th>
          <SorterField property="creation_date" label="Data zgłoszenia"/>
        </th>
        <th>
          <SorterField property="modification_date" label="Data modyfikacji"/>
        </th>
      </tr>
    </thead>
    <form>
      <tbody>
        <tr v-for="defect of defects" :key="defect.id">
          <input type='checkbox' name='names[]' :id="'defect_checkbox_' + defect.id" :value="defect.id">
          <td class="align-middle">
            <a class="btn-link" :href="'/defect/' + defect.id">{{ defect.title }}</a>
          </td>
          <td class="text-center align-middle">
            {{ defect.place }}
          </td>
          <td class="align-middle" :style="defect.status_color">
            {{ defect.state }}
          </td>
          <td>
            {{ defect.creation_date }}
          </td>
          <td>
            {{ defect.last_modification }}
          </td>
        </tr>
        <tr v-if="!visibleDefects.length" class="text-center">
          <td colspan="5">
            <em class="text-muted">Brak widocznych usterek.</em>
          </td>
        </tr>
      </tbody>
    </form>
  </table>
</template>
