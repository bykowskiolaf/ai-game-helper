ProxiHUD = {}
ProxiHUD.name = "ProxiHUD_Bridge"

function ProxiHUD.OnPlayerUnloaded()
    -- Helper to get slotted skills
    local function GetSkills(hotbarCategory)
        local skills = {}
        for i = 3, 8 do -- Indices 3-7 are abilities, 8 is Ultimate
            local slotId = GetSlotBoundId(i, hotbarCategory)
            if slotId > 0 then
                table.insert(skills, GetAbilityName(slotId))
            end
        end
        return skills
    end

    -- Helper to get active quests
    local function GetActiveQuests()
        local quests = {}
        for i = 1, GetNumJournalQuests() do
            local name, _, _, stepText = GetJournalQuestInfo(i)
            if name and name ~= "" then
                table.insert(quests, name) -- We could add stepText too if we want more detail
            end
        end
        return quests
    end

    ProxiHUD_Data = {
        timestamp = os.time(),
        name = GetUnitName("player"),
        level = GetUnitLevel("player"),
        cp = GetUnitChampionPoints("player"),
        race = GetUnitRace("player"),
        class = GetUnitClass("player"),
        role = GetSelectedLFGRole(),

        -- NEW: Location
        zone = GetUnitZone("player"),
        subzone = GetMapName(),

        -- NEW: Attributes
        stats = {
            magicka = GetPlayerStat(STAT_MAGICKA_MAX),
            health = GetPlayerStat(STAT_HEALTH_MAX),
            stamina = GetPlayerStat(STAT_STAMINA_MAX)
        },

        -- NEW: Abilities (Main Bar only for now)
        skills = GetSkills(HOTBAR_CATEGORY_PRIMARY),

        -- NEW: Quests
        quests = GetActiveQuests(),

        -- Existing Gear Logic
        equipment = {}
    }

    -- Scan Equipment (Your existing loop)
    for i = 0, 18 do
        local link = GetItemLink(BAG_WORN, i)
        if link ~= "" then
            table.insert(ProxiHUD_Data.equipment, {
                slot = i,
                name = GetItemLinkName(link),
                link = link
            })
        end
    end
end

EVENT_MANAGER:RegisterForEvent(ProxiHUD.name, EVENT_PLAYER_DEACTIVATED, ProxiHUD.OnPlayerUnloaded)