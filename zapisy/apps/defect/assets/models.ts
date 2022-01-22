export interface DefectInfo {
    id: number,
    name: string,
    creation_date: Date,
    last_modification: Date,
    place: string,
    state: State,
    selected: boolean,
    state_id: 0 | 1 | 2 | 3,
    status_color: string
}

export type State = "Zgłoszone" | "Nie da się" | "Dłuższy problem" | "Zrobione"

export interface KVDict {
  [key: number]: string;
}