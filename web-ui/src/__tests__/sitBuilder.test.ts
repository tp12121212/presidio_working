import { groupKeywords } from "../utils/sitBuilder";

describe("groupKeywords", () => {
  it("groups keywords into a single list", () => {
    expect(groupKeywords(["a", "b"], "single")).toEqual([["a", "b"]]);
  });

  it("splits keywords into separate lists", () => {
    expect(groupKeywords(["a", "b"], "split")).toEqual([["a"], ["b"]]);
  });
});
